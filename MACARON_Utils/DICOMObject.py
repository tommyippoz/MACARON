from MACARON_Utils.DICOM_utils import load_DICOM


class DICOMObject:
    """
    The class containing all information related to a single DICOM (of any type)
    """

    def __init__(self, dicom_file):
        """
        Constructor for DICOMObject
        :param dicom_file: the path to the DICOM
        """
        self.file_name = dicom_file
        self.dicom_ob, self.dicom_type = load_DICOM(dicom_file)

    def __init__(self, dicom_file, dicom_ob, dicom_type):
        """
        Constructor for DICOMObject
        :param dicom_file: the path to the DICOM
        :param dicom_ob: the FileDataset object
        :param dicom_type: the DICOMType type
        """
        self.file_name = dicom_file
        self.dicom_ob = dicom_ob
        self.dicom_type = dicom_type

    def get_file_name(self):
        """
        The filename the DICOMObject was loaded from
        :return: the filename string
        """
        return self.file_name

    def get_object(self):
        """
        Gets the FileDataset object
        :return: the FileDataset object
        """
        return self.dicom_ob

    def get_type(self):
        """
        Gets the type of the DICOMObject
        :return: a DICOMType object
        """
        return self.dicom_type
