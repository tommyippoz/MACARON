from dicompylercore import dicomparser, dvh, dvhcalc

from MACARON_Utils.DICOM_utils import load_DICOM, sanitize_DICOM

dp = dicomparser.DicomParser("DICOM_Files/ADAM_StrctrSets.dcm")

# i.e. Get a dict of structure information
structures = dp.GetStructures()

structures[5]

sanitize_DICOM("DICOM_Files/ADAM_staticoDIAM_Dose.dcm")

# Access DVH data
rtdose = dicomparser.DicomParser("DICOM_Files/ADAM_staticoDIAM_Dose.dcm")
#dose_ob, dose_type = load_DICOM("DICOM_Files/ADAM_staticoDIAM_Dose.dcm")
heartdvh = dvh.DVH.from_dicom_dvh(rtdose.ds, 5)

heartdvh.describe()


# Calculate a DVH from DICOM RT data
calcdvh = dvhcalc.get_dvh("DICOM_Files/ADAM_StrctrSets.dcm", "DICOM_Files/ADAM_staticoDIAM_Dose.dcm", 5)

calcdvh.max, calcdvh.min, calcdvh.D2cc