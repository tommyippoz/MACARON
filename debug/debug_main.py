import os.path

from MACARON_Utils.DICOM_Group import DICOMGroup
from MACARON_Utils.DICOM_Study import DICOMStudy
from MACARON_Utils.general_utils import clear_folder

MAIN_FOLDER = "../DICOM_Files"
TMP_FOLDER = "tmp"
OUTPUT_FOLDER = "output"

if __name__ == "__main__":

    # Checking and clearing TMP_FOLDER
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)
    else:
        clear_folder(TMP_FOLDER)

    # Checking OUTPUT_FOLDER
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    if os.path.exists(MAIN_FOLDER) and os.path.isdir(MAIN_FOLDER):

        for subfolder_name in os.listdir(MAIN_FOLDER):

            subfolder_path = MAIN_FOLDER + "/" + subfolder_name

            if os.path.isdir(subfolder_path):

                # Loading DICOMs
                dg = DICOMGroup(dicom_folder=subfolder_path, group_name=subfolder_name, tmp_folder=TMP_FOLDER)
                # dg.load_folder()
                #
                # # Getting structures for the patient
                # structures = dg.get_structures()
                #
                # # Getting DVH for the patient, a line for each structure
                # dvhs, plot = dg.generate_DVH()
                # dg.print_dvh(output_folder=OUTPUT_FOLDER)
                #
                # # Getting treatment Plan
                # plan, rt_plan = dg.get_plan()
                #
                # # Calculating radiomic features
                # radiomic_features = dg.calculate_radiomics()
                #
                # # Calculating RTPlan metrics
                # rtp_metrics = dg.calculate_RTPlan_metrics(output_folder=OUTPUT_FOLDER)
                dg.report(studies=[e for e in DICOMStudy], output_folder=OUTPUT_FOLDER)
                print("THE END")
            else:
                print("File '" + subfolder_path + "' won't be processed as DICOM source: not a directory")

    else:
        print("Folder '" + MAIN_FOLDER + "' does not exist or it is not a folder")