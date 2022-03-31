import os
import SimpleITK
import pylab

from dicompylercore import dvhcalc
from radiomics import featureextractor

from MACARON_Utils import DICOM_utils
from MACARON_Utils.DICOMType import DICOMType
from MACARON_Utils.DICOMObject import DICOMObject
from MACARON_Utils.DICOM_utils import load_DICOM
from MACARON_Utils.general_utils import create_CT_NRRD, create_mask_NRRD


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
        self.dvhs = {}
        self.radiomics = {}

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

    def get_structures(self):
        """
        Extracts structures from the RT_STRUCTURE file of the DICOMGroup
        :return: a dictionary containing structures
        """
        if self.rts_object is not None:
            structures = DICOM_utils.get_structures(self.rts_object.get_file_name())
            return structures
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
            if self.dvhs == {}:
                print("Need to generate DVHs first, this may take a while...")
                self.generate_DVH()
            structures = self.get_structures()
            for key, structure in structures.items():
                if (key in self.dvhs) and (len(self.dvhs[key].counts) and self.dvhs[key].counts[0] != 0):
                    a = self.dvhs[key].counts * 100 / self.dvhs[key].counts[0]
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
            plan, rt_plan = DICOM_utils.get_plan(self.rtp_object.get_file_name())
            return plan, rt_plan
        else:
            return {}, {}

    def calculate_radiomics(self):
        source_nrrd = self.tmp_folder + "/" + self.name + "_ct.nrrd"
        mask_nrrd = self.tmp_folder + "/" + self.name + "_mask.nrrd"
        if not os.path.exists(source_nrrd):
            print("Need to generate CT NRRD temporary file first")
            create_CT_NRRD(ct_folder=self.folder, nrrd_filename=source_nrrd)
        if not os.path.exists(mask_nrrd):
            print("Need to generate mask NRRD temporary file first")
            create_mask_NRRD(ct_folder=self.folder, nrrd_filename=mask_nrrd,
                             rt_struct_filename=self.rts_object.get_file_name())
        settings = {'binWidth': 25,
                    'resampledPixelSpacing': None,
                    'interpolator': SimpleITK.sitkBSpline}

        # Initialize feature extractor
        extractor = featureextractor.RadiomicsFeatureExtractor(**settings)
        extractor.enableAllFeatures()
        self.radiomics = extractor.execute(source_nrrd, mask_nrrd)
        return self.radiomics



