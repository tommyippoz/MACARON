import os

import pylab
from dicompylercore import dvhcalc

from MACARON_Utils import DICOM_utils
from MACARON_Utils.DICOMType import DICOMType
from MACARON_Utils.DICOMObject import DICOMObject
from MACARON_Utils.DICOM_utils import load_DICOM


class DICOMGroup:
    """
    Class that contains information of a set of DICOM, including TC, RT_STRUCT, RT_DOSE, RT_PLAN
    """

    def __init__(self, dicom_folder):
        """
        Initializes a DICOMGroup to null
        :param dicom_folder: the folder to read the DICOMGroup from
        """
        self.folder = dicom_folder
        self.rts_object = None
        self.rtd_object = None
        self.rtp_object = None
        self.tc_sequence = []
        self.dvhs = {}

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

    def print_dvh(self, output_file):
        """
        Prints the DVH to a file as a PNG
        :param output_file: the file to print the DVH to
        """
        if self.dvhs == {}:
            print("Need to generate DVHs first, this may take a while...")
            self.generate_DVH()
        structures = self.get_structures()
        for key, structure in structures.items():
            if (key in self.dvhs) and (len(self.dvhs[key].counts) and self.dvhs[key].counts[0] != 0):
                pylab.plot(self.dvhs[key].counts * 100 / self.dvhs[key].counts[0],
                           color=dvhcalc.np.array(structure['color'], dtype=float) / 255,
                           label=structure['name'],
                           linestyle='dashed')
        pylab.xlabel('Distance (cm)')
        pylab.ylabel('Percentage Volume')
        pylab.legend(loc=7, borderaxespad=-5)
        pylab.setp(pylab.gca().get_legend().get_texts(), fontsize='x-small')
        pylab.savefig(output_file, dpi=75)

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



