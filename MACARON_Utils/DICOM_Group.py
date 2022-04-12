import os
import SimpleITK
import pylab

from dicompylercore import dvhcalc
from radiomics import featureextractor

from MACARON_Utils import DICOM_utils
from MACARON_Utils.DICOMType import DICOMType
from MACARON_Utils.DICOMObject import DICOMObject
from MACARON_Utils.DICOM_Study import DICOMStudy
from MACARON_Utils.DICOM_utils import load_DICOM, build_DVH_info
from MACARON_Utils.general_utils import create_CT_NRRD, create_masks_NRRD, write_dict, clear_folder

import matplotlib.pyplot as plt

from complexity.PyComplexityMetric import (
    PyComplexityMetric,
    MeanAreaMetricEstimator,
    AreaMetricEstimator,
    ApertureIrregularityMetric)

from complexity.dicomrt import RTPlan


class DICOMGroup:
    """
    Class that contains information of a set of DICOM, including TC, RT_STRUCT, RT_DOSE, RT_PLAN
    """

    def __init__(self, dicom_folder, group_name, tmp_folder):
        """
        Initializes a DICOMGroup to null
        :param dicom_folder: the folder to read the DICOMGroup from
        """
        self.folder = dicom_folder
        self.name = group_name
        self.tmp_folder = tmp_folder
        self.rts_object = None
        self.rtd_object = None
        self.rtp_object = None
        self.tc_sequence = []
        self.structures = None
        self.dvhs = None
        self.radiomics = None
        self.plan_details = None
        self.plan_metrics = None

    def get_name(self):
        return self.name

    def load_folder(self):
        """
        Loads the DICOMGroup from a folder, initializing all class attributes but dvh
        """
        if os.path.exists(os.path.dirname(self.folder)):
            for dicom_file in os.listdir(self.folder):
                if dicom_file.endswith(("dcm", "DCM", "dicom", "DICOM")):
                    dicom_file = self.folder + "/" + dicom_file
                    f_ob, f_type = load_DICOM(dicom_file)
                    if f_type == DICOMType.RT_PLAN:
                        self.rtp_object = DICOMObject(dicom_file, f_ob, f_type)
                    elif f_type == DICOMType.RT_STRUCT:
                        self.rts_object = DICOMObject(dicom_file, f_ob, f_type)
                    elif f_type == DICOMType.RT_DOSE:
                        self.rtd_object = DICOMObject(dicom_file, f_ob, f_type)
                    elif f_type == DICOMType.TC:
                        self.tc_sequence.append(DICOMObject(dicom_file, f_ob, f_type))
                    else:
                        print("Unable to decode file '" + dicom_file + "'")
        else:
            print("Folder '" + self.folder + "' does not exist")
        return (self.rtp_object is not None) and (self.rts_object is not None) \
               and (self.rtd_object is not None) and (self.tc_sequence is not None)

    def get_structures(self):
        """
        Extracts structures from the RT_STRUCTURE file of the DICOMGroup
        :return: a dictionary containing structures
        """
        if self.rts_object is not None:
            self.structures = DICOM_utils.get_structures(self.rts_object.get_file_name())
            return self.structures
        else:
            return {}

    def generate_DVH(self):
        """
        Generates Dose-Volume Histogram (DVH) for the DICOMGroup and stores it in the dvh attribute
        :return: a dictionary containing the data to build a dvh
        """
        if self.rts_object is not None:
            if self.rtd_object is not None:
                structures = self.get_structures()
                self.dvhs = {}
                for key, structure in structures.items():
                    self.dvhs[key] = dvhcalc.get_dvh(self.rts_object.get_file_name(),
                                                     self.rtd_object.get_file_name(),
                                                     key)
                    if (key in self.dvhs) and (len(self.dvhs[key].counts) and self.dvhs[key].counts[0] != 0):
                        print('DVH found for structure ' + structure['name'])
            else:
                print("No RT_DOSE file in the group")
        else:
            print("No RT_STRUCTURE file in the group")
        return self.dvhs, pylab.figure()

    def print_dvh(self, output_folder):
        """
        Prints the DVH to a file as a PNG
        :param output_folder: the folder to print the DVH to
        """
        if os.path.exists(output_folder) and os.path.isdir(output_folder):
            dvh_path = output_folder + "/" + self.name + "_DVH.png"
            if self.dvhs is None:
                print("Need to generate DVHs first, this may take a while...")
                self.generate_DVH()
            if self.structures is None:
                self.get_structures()
            for key, structure in self.structures.items():
                if (key in self.dvhs) and (len(self.dvhs[key].counts) and self.dvhs[key].counts[0] != 0):
                    pylab.plot(self.dvhs[key].counts * 100 / self.dvhs[key].counts[0],
                               color=dvhcalc.np.array(structure['color'], dtype=float) / 255,
                               label=structure['name'],
                               linestyle='dashed')
            pylab.xlabel('Distance (cm)')
            pylab.ylabel('Percentage Volume')
            pylab.legend(loc=7, borderaxespad=-5)
            pylab.setp(pylab.gca().get_legend().get_texts(), fontsize='x-small')
            pylab.savefig(dvh_path, dpi=75)
        else:
            print("'" + output_folder + "' is not a valid destination folder")

    def get_plan(self):
        """
        Gets the RT_PLAN from the DICOMGroup
        :return: a dictionary containing the detail of the RT_PLAN, and a supporting string
        """
        if self.rtp_object is not None:
            self.plan_details, rt_plan = DICOM_utils.get_plan(self.rtp_object.get_file_name())
            return self.plan_details, rt_plan
        else:
            return {}, {}

    def calculate_radiomics(self):
        source_nrrd = self.tmp_folder + "/" + self.name + "_ct.nrrd"
        mask_folder = self.tmp_folder + "/" + self.name + "_masks"
        if not os.path.exists(source_nrrd):
            print("Need to generate CT NRRD temporary file first")
            create_CT_NRRD(ct_folder=self.folder, nrrd_filename=source_nrrd)
        if not os.path.exists(mask_folder):
            print("Need to generate mask NRRD temporary file first")
            create_masks_NRRD(tmp_folder=self.tmp_folder, ct_nrrd_filename=source_nrrd,
                              rt_struct_filename=self.rts_object.get_file_name(),
                              name=self.name, rt_dose_filename=self.rtd_object.get_file_name())
        settings = {'binWidth': 25,
                    'resampledPixelSpacing': None,
                    'interpolator': SimpleITK.sitkBSpline}

        # Initialize feature extractor
        extractor = featureextractor.RadiomicsFeatureExtractor(**settings)
        extractor.enableAllFeatures()
        self.radiomics = {}
        for file in os.listdir(mask_folder):
            mask_nrrd = mask_folder + "/" + file
            if os.path.isfile(mask_nrrd) and file.endswith(".nrrd"):
                file = file.replace(".nrrd", "")
                print("Calculating Radiomic features for '" + self.name + "', structure '" + file + "'")
                self.radiomics[file] = extractor.execute(source_nrrd, mask_nrrd)
        return self.radiomics

    DEFAULT_RTP_METRICS = [
        PyComplexityMetric,
        MeanAreaMetricEstimator,
        AreaMetricEstimator,
        ApertureIrregularityMetric]

    RTP_METRICS_UNITS = {
        PyComplexityMetric: "CI [mm^-1]",
        MeanAreaMetricEstimator: "mm^2",
        AreaMetricEstimator: "mm^2",
        ApertureIrregularityMetric: "dimensionless"}

    def calculate_RTPlan_metrics(self, metrics_list=None, generate_plots=True, output_folder=None):
        """
        Calculates Complexity indexes from RTPlan
        :param output_folder: folder to print plots to
        :param generate_plots: True if plots have to be generated and saved to file
        :param metrics_list: the list of metrics to be calculated, initialized as DEFAULT_RTP_METRICS when missing
        :return: a dictionary containing the metric value and the unit for each RTPlan metric
        """
        if (metrics_list is None) or (type(metrics_list) is not list):
            metrics_list = self.DEFAULT_RTP_METRICS

        self.plan_metrics = {}
        plan_info = RTPlan(filename=self.rtp_object.get_file_name())
        if plan_info is not None:
            plan_dict = plan_info.get_plan()
            for metric in metrics_list:
                unit = self.RTP_METRICS_UNITS[metric]
                met_obj = metric()
                plan_metric = met_obj.CalculateForPlan(None, plan_dict)
                self.plan_metrics[metric.__name__] = [plan_metric, unit]
                if generate_plots:
                    for k, beam in plan_dict["beams"].items():
                        fig, ax = plt.subplots()
                        cpx_beam_cp = met_obj.CalculateForBeamPerAperture(None, plan_dict, beam)
                        ax.plot(cpx_beam_cp)
                        ax.set_xlabel("Control Point")
                        ax.set_ylabel(f"${unit}$")
                        txt = f"Patient: {self.name} - {metric.__name__} per control point"
                        ax.set_title(txt)
                        if output_folder is not None:
                            fig.savefig(output_folder + "/" + self.name + "_" + metric.__name__ + ".png",
                                        dpi=fig.dpi)
                        else:
                            fig.savefig(self.name + "_" + metric.__name__ + ".png", dpi=fig.dpi)
        else:
            print("Supplied file is not an RT_PLAN")
        return self.plan_metrics

    def report(self, studies, output_folder, clean_folder=True):
        if os.path.exists(output_folder) and os.path.isdir(output_folder):
            group_folder = output_folder + "/" + self.name + "/"
            if os.path.exists(group_folder):
                if clean_folder:
                    print("Deleting existing info inside '" + group_folder + "' folder")
                    clear_folder(group_folder)
            else:
                os.makedirs(group_folder)
            if len(self.tc_sequence) == 0:
                print("Loading info from DICOM set")
                self.load_folder()
            if (studies is not None) and (len(studies) > 0):
                for study in studies:
                    if study is DICOMStudy.STRUCTURES:
                        out_file = group_folder + "structures.csv"
                        if self.structures is None:
                            self.get_structures()
                        write_dict(dict_obj=self.structures, filename=out_file,
                                   header="structure_id,id,name,type,color,empty")
                    elif study is DICOMStudy.PLAN_DETAIL:
                        out_file = group_folder + "plan_detail.csv"
                        if self.plan_details is None:
                            self.get_plan()
                        write_dict(dict_obj=self.plan_details, filename=out_file, header="attribute,value")
                    elif study is DICOMStudy.PLAN_METRICS_DATA:
                        out_file = group_folder + "plan_metrics.csv"
                        if self.plan_metrics is None:
                            self.calculate_RTPlan_metrics()
                        write_dict(dict_obj=self.plan_metrics, filename=out_file, header="metric,value,unit")
                    elif study is DICOMStudy.PLAN_METRICS_IMG:
                        self.calculate_RTPlan_metrics(output_folder=group_folder)
                    elif study is DICOMStudy.RADIOMIC_FEATURES:
                        out_file = group_folder + "radiomic_features.csv"
                        if self.radiomics is None:
                            self.calculate_radiomics()
                        write_dict(dict_obj=self.radiomics, filename=out_file, header="structure,feature,value")
                    elif study is DICOMStudy.DVH_IMG:
                        self.print_dvh(output_folder=group_folder)
                    elif study is DICOMStudy.DVH_DATA:
                        if self.dvhs is None:
                            self.generate_DVH()
                        for dvh_id in self.dvhs.keys():
                            out_file = group_folder + "dvh_data_structure_" + str(dvh_id) + ".csv"
                            write_dict(dict_obj=build_DVH_info(self.dvhs[dvh_id]),
                                       filename=out_file, header="attribute,value")
                    else:
                        print("Cannot recognize study '" + study + "' to report about")
            else:
                print("No valid studies to report. Please input a list containing DICOMStudy objects")
        else:
            print("Folder '" + output_folder + "' does not exist or is not a folder")

