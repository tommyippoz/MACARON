import copy
import math
import os
import SimpleITK
import numpy
import pylab

from dicompylercore import dvhcalc
from radiomics import featureextractor

from MACARON_Utils import DICOM_utils
from MACARON_Utils.DICOMType import DICOMType
from MACARON_Utils.DICOMObject import DICOMObject
from MACARON_Utils.DICOM_Study import DICOMStudy
from MACARON_Utils.DICOM_utils import load_DICOM, build_DVH_info, extractPatientData
from MACARON_Utils.general_utils import create_masks_NRRD, write_dict, clear_folder, create_CT_NRRD, complexity_indexes, \
    create_mask_NRRD, test_NRRD, compute_metrics_stat

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
        self.rtp_objects = []
        self.tc_sequence = []
        self.structures = None
        self.dvhs = None
        self.radiomics = None
        self.radiomics_dose = None
        self.plan_details = None
        self.plan_metrics = None
        self.plan_custom_metrics = None
        self.isodose_file = None
        self.radiomics_isodose = None

    def get_folder(self):
        return self.folder

    def get_name(self):
        return self.name

    def get_rtp_objects(self):
        return self.rtp_objects

    def load_folder(self):
        """
        Loads the DICOMGroup from a folder, initializing all class attributes but dvh
        """
        self.rtp_objects = []
        if os.path.exists(os.path.dirname(self.folder)):
            for dicom_file in os.listdir(self.folder):
                if dicom_file.endswith(("dcm", "DCM", "dicom", "DICOM")):
                    dicom_file = self.folder + "/" + dicom_file
                    f_ob, f_type = load_DICOM(dicom_file)
                    if f_type == DICOMType.RT_PLAN:
                        self.rtp_objects.append(DICOMObject(dicom_file, f_ob, f_type))
                        if hasattr(f_ob, "PatientName"):
                            self.name = str(f_ob.PatientName)
                    elif f_type == DICOMType.RT_STRUCT:
                        self.rts_object = DICOMObject(dicom_file, f_ob, f_type)
                    elif f_type == DICOMType.RT_DOSE:
                        self.rtd_object = DICOMObject(dicom_file, f_ob, f_type)
                    elif f_type == DICOMType.TC:
                        self.tc_sequence.append(DICOMObject(dicom_file, f_ob, f_type))
                    else:
                        print("Unable to decode file '" + dicom_file + "'")
                elif dicom_file.endswith(("nrrd", "NRRD")):
                    self.isodose_file =  self.folder + "/" + dicom_file
        else:
            print("Folder '" + self.folder + "' does not exist")
        return (len(self.rtp_objects) > 0) or (self.rts_object is not None) \
               or (self.rtd_object is not None) or (self.tc_sequence is not None and len(self.tc_sequence) > 0)

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

    def get_patient_info(self):
        """
        Extracts patient data from DICOM Group
        """
        if len(self.rtp_objects) > 0:
            return extractPatientData(self.rtp_objects[0].get_object())
        else:
            return None

    def get_dose_info(self):
        """
        Extracts dose data from DICOM Group
        """
        if self.rtd_object is not None:
            return DICOM_utils.extractDoseData(self.rtd_object.get_object())
        else:
            return None

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
            if self.structures is not None:
                for key, structure in self.structures.items():
                    if (key in self.dvhs) and (len(self.dvhs[key].counts) and self.dvhs[key].counts[0] != 0):
                        pylab.plot(self.dvhs[key].counts * 100 / self.dvhs[key].counts[0],
                                   color=dvhcalc.np.array(structure['color'], dtype=float) / 255,
                                   label=structure['name'],
                                   linestyle='dashed')
                pylab.xlabel('Dose')
                pylab.ylabel('Percentage Volume')
                pylab.legend(loc=7, borderaxespad=-5)
                pylab.setp(pylab.gca().get_legend().get_texts(), fontsize='x-small')
                pylab.savefig(dvh_path, dpi=75)
            else:
                print("Unable to compute DVH: no RT_STRUCT file")
            return dvh_path
        else:
            print("'" + output_folder + "' is not a valid destination folder")
            return ""

    def get_plan(self):
        """
        Gets the RT_PLAN from the DICOMGroup
        :return: a dictionary containing the detail of the RT_PLAN, and a supporting string
        """
        if len(self.rtp_objects) > 0:
            self.plan_details = []
            rt_plans = []
            for plan in self.rtp_objects:
                plan_det, rt_plan = DICOM_utils.get_plan(plan.get_file_name())
                if hasattr(plan_det, "date") and len(plan_det["date"]) == 0:
                    plan_det["date"] = plan.get_object().InstanceCreationDate
                else:
                    plan_det["date"] = "1900-01-01"
                if hasattr(plan_det, "time") and len(plan_det["time"]) == 0:
                    plan_det["time"] = plan.get_object().InstanceCreationTime
                else:
                    plan_det["time"] = 1
                if hasattr(plan_det, "label") and len(plan_det["label"]) == 0:
                    plan_det["label"] = plan.get_object().RTPlanLabel
                else:
                    plan_det["label"] = self.name
                if hasattr(plan_det, "name") and len(plan_det["name"]) == 0:
                    plan_det["name"] = plan.get_object().RTPlanName
                else:
                    plan_det["name"] = self.name

                self.plan_details.append(plan_det)
                rt_plans.append(rt_plan)

            return self.plan_details, rt_plans
        else:
            return [], []

    def calculate_radiomics(self):
        source_nrrd = self.tmp_folder + "/" + self.name + "_ct.nrrd"
        mask_folder = self.tmp_folder + "/" + self.name + "_masks"
        if self.rts_object is not None:
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
        else:
            self.radiomics = {}
            print("Cannot compute radiomic features: Missing RT_STRUCT file")
        return self.radiomics

    def calculate_dose_radiomics(self):
        source_nrrd = self.tmp_folder + "/" + self.name + "_dose.nrrd"
        ct_nrrd = self.tmp_folder + "/" + self.name + "_ct.nrrd"
        mask_folder = self.tmp_folder + "/" + self.name + "_masks"
        if self.rtd_object is not None:
            if not os.path.exists(ct_nrrd):
                print("Need to generate CT NRRD temporary file first")
                create_CT_NRRD(ct_folder=self.folder, nrrd_filename=ct_nrrd)
            if not os.path.exists(source_nrrd):
                print("Need to generate DOSE NRRD temporary file first")
                test_NRRD(nrrd_filename=source_nrrd, base_file=self.rtd_object.get_file_name(),
                          ct_nrrd_filename=ct_nrrd)
            if not os.path.exists(mask_folder):
                print("Need to generate mask NRRD temporary file first")
                create_masks_NRRD(tmp_folder=self.tmp_folder, ct_nrrd_filename=ct_nrrd,
                                  rt_struct_filename=self.rts_object.get_file_name(),
                                  name=self.name, rt_dose_filename=self.rtd_object.get_file_name())
            settings = {'binWidth': 25,
                        'resampledPixelSpacing': None,
                        'interpolator': SimpleITK.sitkBSpline}

            # Initialize feature extractor
            extractor = featureextractor.RadiomicsFeatureExtractor(**settings)
            extractor.enableAllFeatures()
            self.radiomics_dose = {}
            for file in os.listdir(mask_folder):
                mask_nrrd = mask_folder + "/" + file
                if os.path.isfile(mask_nrrd) and file.endswith(".nrrd"):
                    file = file.replace(".nrrd", "")
                    print("Calculating Radiomic Dose features for '" + self.name + "', structure '" + file + "'")
                    self.radiomics_dose[file] = extractor.execute(source_nrrd, mask_nrrd)
        else:
            self.radiomics_dose = {}
            print("Cannot compute radiomic features for dose: Missing RT_DOSE file")
        return self.radiomics_dose

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

        self.plan_metrics = []
        img_paths = []
        if len(self.rtp_objects) > 0:
            for plan in self.rtp_objects:
                pm = {}
                plan_imgs = {}
                plan_info = RTPlan(filename=plan.get_file_name())
                if plan_info is not None:
                    plan_dict = plan_info.get_plan()
                    for metric in metrics_list:
                        unit = self.RTP_METRICS_UNITS[metric]
                        met_obj = metric()
                        plan_metric = met_obj.CalculateForPlan(None, plan_dict)
                        pm[metric.__name__] = [plan_metric, unit]
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
                                    img_path = output_folder + "/" + self.name + "_" + metric.__name__ + ".png"
                                else:
                                    img_path = self.name + "_" + metric.__name__ + ".png"
                                fig.savefig(img_path, dpi=fig.dpi)
                                plan_imgs[metric.__name__] = img_path
                    self.plan_metrics.append(pm)
                    img_paths.append(plan_imgs)
                else:
                    print("Supplied file is not an RT_PLAN")
        return self.plan_metrics, img_paths

    def calculate_RTPlan_custom_metrics(self):
        """
        Calculates Complexity indexes from RTPlan
        :return: a dictionary containing the metric value and the unit for each RTPlan metric
        """
        self.plan_custom_metrics = []

        if len(self.rtp_objects) > 0:

            for plan in self.rtp_objects:

                rt_ob = plan.get_object()
                if rt_ob is not None:

                    plan_dict = RTPlan(filename=plan.get_file_name()).get_plan()
                    beam_index = 1
                    pcm = {}

                    for beam in list(plan_dict["beams"].values()):

                        beam_name = "Beam" + str(beam_index)
                        beam_mu = float(beam['MU'])
                        beam_final_ms_weight = float(beam['FinalCumulativeMetersetWeight'])
                        pcm[beam_name] = {"Sequence": [], "MUbeam": beam_mu, "MUfinalweight": beam_final_ms_weight}

                        item_index = 0
                        left_jaws = []
                        right_jaws = []
                        for item in beam["ControlPointSequence"]:
                            item_index += 1
                            cp_mu = float(item['CumulativeMetersetWeight'].value)
                            if hasattr(item, "BeamLimitingDevicePositionSequence"):
                                if len(item.BeamLimitingDevicePositionSequence) == 3:
                                    y_data = item.BeamLimitingDevicePositionSequence[1].LeafJawPositions
                                    lj_arr = item.BeamLimitingDevicePositionSequence[2].LeafJawPositions
                                else:
                                    y_data = item.BeamLimitingDevicePositionSequence[0].LeafJawPositions
                                    lj_arr = item.BeamLimitingDevicePositionSequence[1].LeafJawPositions
                                cm, left, right = complexity_indexes(y_data, lj_arr)
                                left_jaws.append(left)
                                right_jaws.append(right)
                                if cm is not None:
                                    cm["index"] = item_index
                                    if item_index < len(beam["ControlPointSequence"]):
                                        next_cp_mu = float(beam["ControlPointSequence"][item_index]['CumulativeMetersetWeight'].value)
                                        cm["MU"] = (next_cp_mu - cp_mu)*beam_mu/beam_final_ms_weight
                                    else:
                                        cm["MU"] = 0
                                    cm["MUrel"] = cm["MU"] / beam_mu
                                    cm["MUcumrel"] = cp_mu + cm["MUrel"]
                                pcm[beam_name]["Sequence"].append(cm)
                            else:
                                print("Item " + str(item_index) + "of beam " + str(beam_index) + " not properly formatted")
                        beam_index += 1

                        # Compute Additional Beam metrics: M
                        M = 0
                        for cp_metrics in pcm[beam_name]["Sequence"]:
                            M = M + cp_metrics["MU"] * cp_metrics["perimeter"] / cp_metrics["area"]
                        pcm[beam_name]["M"] = M / pcm[beam_name]["MUbeam"]

                        # Compute Additional CP/Beam metrics: AAV
                        left_jaws = numpy.asarray(left_jaws)
                        right_jaws = numpy.asarray(right_jaws)
                        norm_factor = sum(abs(numpy.max(right_jaws, axis=0) - numpy.min(left_jaws, axis=0)))
                        for i in range(len(pcm[beam_name]["Sequence"])):
                            pcm[beam_name]["Sequence"][i]["AAV"] = \
                                pcm[beam_name]["Sequence"][i]["sumAllApertures"] / norm_factor

                        # Compute Additional Beam metrics: MCS
                        MCS = 0
                        for cp_metrics in pcm[beam_name]["Sequence"]:
                            MCS = MCS + cp_metrics["AAV"] * cp_metrics["LSV"] * cp_metrics["MUrel"]
                        pcm[beam_name]["MCS"] = MCS

                        # Compute Additional Beam metrics: MCSV
                        MCSV = 0
                        for i in range(len(pcm[beam_name]["Sequence"]) - 1):
                            cpi = pcm[beam_name]["Sequence"][i]
                            cpi1 = pcm[beam_name]["Sequence"][i + 1]
                            MCSV = MCSV + (cpi["AAV"] + cpi1["AAV"]) / 2 * (cpi["LSV"] + cpi1["LSV"]) / 2 * cpi["MUrel"]
                        pcm[beam_name]["MCSV"] = MCSV

                        # Compute Additional Beam metrics: MFC
                        MFC = 0
                        for cp_metrics in pcm[beam_name]["Sequence"]:
                            MFC = MFC + cp_metrics["area"] * cp_metrics["MUrel"]
                        pcm[beam_name]["MFC"] = MFC

                        # Compute Additional Beam metrics: BI
                        BI = 0
                        for cp_metrics in pcm[beam_name]["Sequence"]:
                            BI = BI + cp_metrics["MUrel"] * (math.pow(cp_metrics["perimeter"], 2) / (4 * math.pi * cp_metrics["area"]))
                        pcm[beam_name]["BI"] = BI

                        # Compute Additional Beam metrics: average aperture less than 10mm / 1cm
                        aal10 = 0
                        for cp_metrics in pcm[beam_name]["Sequence"]:
                            if cp_metrics["avgAperture"] <= 10:
                                aal10 = aal10 + 1
                        pcm[beam_name]["avgApertureLessThan1cm"] = aal10

                        # Compute Additional Beam metrics: average aperture less than 10mm / 1cm
                        ydl10 = 0
                        for cp_metrics in pcm[beam_name]["Sequence"]:
                            if cp_metrics["yDiff"] <= 10:
                                ydl10 = ydl10 + 1
                        pcm[beam_name]["yDiffLessThan1cm"] = ydl10

                        # Compute Additional Beam metrics: SAS
                        SAS = {"nAperturesLeq2": 0, "nAperturesLeq5": 0, "nAperturesLeq10": 0, "nAperturesLeq20": 0}
                        for cp_metrics in pcm[beam_name]["Sequence"]:
                            for key in SAS:
                                SAS[key] = SAS[key] + cp_metrics[key] / cp_metrics["nAperturesG0"] * cp_metrics["MUrel"]
                        pcm[beam_name]["SAS2"] = SAS["nAperturesLeq2"]
                        pcm[beam_name]["SAS5"] = SAS["nAperturesLeq5"]
                        pcm[beam_name]["SAS10"] = SAS["nAperturesLeq10"]
                        pcm[beam_name]["SAS20"] = SAS["nAperturesLeq20"]

                    # Computing Plan Metrics
                    beams = copy.deepcopy(list(pcm.keys()))
                    pcm["plan"] = {}

                    MU = 0
                    for beam_name in beams:
                        MU = MU + pcm[beam_name]["MUbeam"]
                    pcm["plan"]["MUplan"] = MU

                    M = 0
                    for beam_name in beams:
                        M = M + pcm[beam_name]["MUbeam"] * pcm[beam_name]["M"]
                    pcm["plan"]["Mplan"] = M / MU

                    MCS = 0
                    for beam_name in beams:
                        MCS = MCS + pcm[beam_name]["MUbeam"] * pcm[beam_name]["MCS"]
                    pcm["plan"]["MCSplan"] = MCS / MU

                    MCSV = 0
                    for beam_name in beams:
                        MCSV = MCSV + pcm[beam_name]["MUbeam"] * pcm[beam_name]["MCSV"]
                    pcm["plan"]["MCSVplan"] = MCSV / MU

                    MFC = 0
                    for beam_name in beams:
                        MFC = MFC + pcm[beam_name]["MUbeam"] * pcm[beam_name]["MFC"]
                    pcm["plan"]["MFCplan"] = MFC / MU

                    PI = 0
                    for beam_name in beams:
                        PI = PI + pcm[beam_name]["MUbeam"] * pcm[beam_name]["BI"]
                    pcm["plan"]["PI"] = PI / MU

                    nCP = 0
                    for beam_name in beams:
                        nCP = nCP + len(pcm[beam_name]["Sequence"])
                    pcm["plan"]["nCP"] = nCP

                    al10 = 0
                    for beam_name in beams:
                        al10 = al10 + pcm[beam_name]["avgApertureLessThan1cm"]
                    pcm["plan"]["avgApertureLessThan1cm"] = al10

                    yl10 = 0
                    for beam_name in beams:
                        yl10 = yl10 + pcm[beam_name]["yDiffLessThan1cm"]
                    pcm["plan"]["yDiffLessThan1cm"] = yl10

                    # Computing statistical indexes of plan metrics
                    # metrics_stat = compute_metrics_stat(pcm, beams)
                    # pcm["plan"].update(metrics_stat)

                    self.plan_custom_metrics.append(pcm)

                else:
                    print("Supplied file is not an RT_PLAN")
        return self.plan_custom_metrics

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
                    elif study is DICOMStudy.DOSE_RADIOMIC_FEATURES:
                        out_file = group_folder + "dose_radiomic_features.csv"
                        if self.radiomics is None:
                            self.calculate_dose_radiomics()
                        write_dict(dict_obj=self.radiomics_dose, filename=out_file, header="structure,feature,value")
                    elif study is DICOMStudy.DVH_IMG:
                        self.print_dvh(output_folder=group_folder)
                    elif study is DICOMStudy.DVH_DATA:
                        if self.dvhs is None:
                            self.generate_DVH()
                        for dvh_id in self.dvhs.keys():
                            out_file = group_folder + "dvh_data_structure_" + str(dvh_id) + ".csv"
                            write_dict(dict_obj=build_DVH_info(self.dvhs[dvh_id]),
                                       filename=out_file, header="attribute,value")
                    elif study is DICOMStudy.CONTROL_POINT_METRICS:
                        self.calculate_RTPlan_custom_metrics()
                        for i in range(0, len(self.plan_custom_metrics)):
                            out_file = group_folder + "plan_custom_complexity_metrics_" + str(i) + ".csv"
                            write_dict(dict_obj=self.plan_custom_metrics[i], filename=out_file,
                                       header="beam,attribute,list_index,metric_name,metric_value")
                    else:
                        print("Cannot recognize study '" + study + "' to report about")
            else:
                print("No valid studies to report. Please input a list containing DICOMStudy objects")
        else:
            print("Folder '" + output_folder + "' does not exist or is not a folder")
