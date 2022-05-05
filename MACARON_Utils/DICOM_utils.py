import pydicom
from dicompylercore import dicomparser, dvhcalc

from MACARON_Utils.DICOMType import DICOMType


def load_DICOM(file_path, sanitize=True):
    """
    Loads a DICOM object from a file
    :param file_path: path to the DICOM file
    :param sanitize: True if a TransferSyntaxUID field may be missing from the DICOM file
    :return: the DICOMObject and its DICOMType
    """
    dicom_ob = pydicom.read_file(file_path, force=True)
    if sanitize and ("TransferSyntaxUID" not in dicom_ob.file_meta):
        sanitize_DICOM(file_path)
        dicom_ob = pydicom.read_file(file_path, force=True)
    dicom_type = get_DICOM_type(dicom_ob)
    return dicom_ob, dicom_type


def sanitize_DICOM(file_path):
    """
    Updates a DICOM file by adding a TransferSyntaxUID parameter (default value)
    :param file_path: file to sanitize
    """
    ds = pydicom.read_file(file_path, force=True)
    if "TransferSyntaxUID" not in ds.file_meta:
        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
        print("Adding parameter 'TransferSyntaxUID' to DICOM")
        pydicom.write_file(file_path, ds)


def extractPatientData(dicom_ob):
    """
    Gets a dictionary with patient data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of patient data
    """
    patient_data = {"ID": dicom_ob.PatientID,
                    "Sex": dicom_ob.PatientSex,
                    "BirthDate": dicom_ob.PatientBirthDate}
    return patient_data


def extractDoseData(dicom_ob):
    """
    Gets a dictionary with dose data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of dose data
    """
    dose_data = {"GridScaling": dicom_ob.DoseGridScaling,
                 "SumType": dicom_ob.DoseSummationType,
                 "Type": dicom_ob.DoseType,
                 "Units": dicom_ob.DoseUnits,
                 "RTPlanSequence": dicom_ob.ReferencedRTPlanSequence}
    return dose_data


def extractStructureData(dicom_ob):
    """
    Gets a dictionary with structures data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of structures data
    """
    structure_data = {"StructureSetSequence": dicom_ob.ReferencedStructureSetSequence}
    return structure_data


def extractManufacturerData(dicom_ob):
    """
    Gets a dictionary with manufacturer data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of manufacturer data
    """
    man_data = {"Name": dicom_ob.Manufacturer,
                "ModelName": dicom_ob.ManufacturerModelName,
                "SW_Version": dicom_ob.SoftwareVersions,
                "CharSet": dicom_ob.SpecificCharacterSet}
    return man_data


def extractStudyData(dicom_ob):
    """
    Gets a dictionary with study data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of patient data
    """
    study_data = {"ID": dicom_ob.StudyID,
                  "UID": dicom_ob.StudyInstanceUID,
                  "Time": dicom_ob.StudyTime,
                  "Date": dicom_ob.StudyDate,
                  "Modality": dicom_ob.Modality,
                  "NumFrames": dicom_ob.NumberOfFrames,
                  "PhotometricInterpretation": dicom_ob.PhotometricInterpretation,
                  "Correction": dicom_ob.TissueHeterogeneityCorrection}
    return study_data


def extractImageData(dicom_ob):
    """
    Gets a dictionary with image data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of image data
    """
    image_data = {"Orientation": dicom_ob.ImageOrientationPatient,
                  "Position": dicom_ob.ImagePositionPatient,
                  "FrameIncrementPointer": dicom_ob.FrameIncrementPointer,
                  "GridOffsetVector": dicom_ob.GridFrameOffsetVector}
    return image_data


def get_DICOM_type(dicom_ob):
    """
    Gets the DICOMType corresponding to the FileDataset object
    :param dicom_ob: the FileDataset object
    :return: the DICOMType
    """
    if dicom_ob is not None:
        if hasattr(dicom_ob, 'StructureSetROISequence'):
            return DICOMType.RT_STRUCT
        elif hasattr(dicom_ob, 'DoseUnits'):
            return DICOMType.RT_DOSE
        elif hasattr(dicom_ob, 'RTPlanDescription'):
            return DICOMType.RT_PLAN
        elif hasattr(dicom_ob, 'CTDIvol'):
            return DICOMType.TC
    return DICOMType.OTHER


def get_DICOM_type_from_ID(dicom_ob):
    """
    Determines the DICOMType of the FileDataset using its SOPClassUID.
    :param dicom_ob: the FileDataset object
    :return: the DICOMType
    """
    uid = getattr(dicom_ob, 'SOPClassUID', None)
    return get_DICOM_type_from_ID(uid)


def get_DICOM_type_from_ID(uid):
    """
    Determines the DICOMType from a SOPClassUID value.
    :param uid: the SOPClassUID value
    :return: the DICOMType
    """
    if uid == '1.2.840.10008.5.1.4.1.1.481.2':
        return DICOMType.RT_DOSE
    elif uid == '1.2.840.10008.5.1.4.1.1.481.3':
        return DICOMType.RT_STRUCT
    elif uid == '1.2.840.10008.5.1.4.1.1.481.5':
        return DICOMType.RT_PLAN
    elif uid == '1.2.840.10008.5.1.4.1.1.2':
        return DICOMType.TC
    else:
        return None


def get_structures(rts_file):
    """
    Extract structures from an RT_STRUCTURE DICOM file
    :param rts_file: the path to the RT_STRUCTURE file
    :return: a dictionary with structures
    """
    rtss = dicomparser.DicomParser(rts_file)
    if get_DICOM_type(rtss.ds) == DICOMType.RT_STRUCT:
        structures = rtss.GetStructures()
        return structures
    else:
        return {}


def get_plan(rtp_file):
    """
    Gets the plan from an RT_PLAN DICOM object
    :param rtp_file: the path to the RT_PLAN file
    :return: a dictionary with the plan, and a string description
    """
    rtp = dicomparser.DicomParser(rtp_file)
    if get_DICOM_type(rtp.ds) == DICOMType.RT_PLAN:
        plan = rtp.GetPlan()
        rt_plan = rtp.GetReferencedRTPlan()
        return plan, rt_plan
    else:
        return {}, {}


def build_DVH_info(dvh):
    dvh_info = {}
    dvh_info["Structure"] = dvh.name
    if dvh.volume_units == '%':
        dvh_info["rel volume"] = dvh.volume
    else:
        dvh_info["abs volume"] = dvh.volume
    dvh_info["type"] = dvh.dvh_type
    dvh_info["volume unit"] = dvh.volume_units
    dvh_info["dose unit"] = dvh.dose_units
    dvh_info["Max Dose"] = dvh.max
    dvh_info["Min Dose"] = dvh.min
    dvh_info["Mean Dose"] = dvh.mean
    dvh_info["D100"] = dvh.D100
    dvh_info["D98"] = dvh.D98
    dvh_info["D95"] = dvh.D95
    if dvh.dose_units == '%':
        dvh_info["V100"] = dvh.V100
        dvh_info["V95"] = dvh.V95
        dvh_info["V5"] = dvh.V5
    dvh_info["D2cc"] = dvh.D2cc
    dvh_info["counts"] = ",".join([str(a) for a in dvh.counts])
    dvh_info["bins"] = ",".join([str(a) for a in dvh.bins])
    #dvh_info["cumulative"] = dvh.cumulative
    return dvh_info
