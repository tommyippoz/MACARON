from MACARON_Utils.DICOM_Group import DICOMGroup

MAIN_FOLDER = "../DICOM_Files"


if __name__ == "__main__":
    # Loading DICOMs
    dg = DICOMGroup(MAIN_FOLDER)
    dg.load_folder()

    # Getting structures for the patient
    structures = dg.get_structures()

    # Getting DVH for the patient, a line for each structure
    dvhs = dg.generate_DVH()
    dg.print_dvh('../output/dvhwx.png')

    # Getting treatment Plan
    plan, rt_plan = dg.get_plan()
    a = 1