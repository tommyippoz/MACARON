import configparser
import os.path

from MACARON_Utils.DICOM_Group import DICOMGroup
from MACARON_Utils.DICOM_Study import DICOMStudy
from MACARON_Utils.general_utils import clear_folder, write_dict

from database import DB_Manager

MAIN_FOLDER = "../DICOM_Files/DicomAnonymized_test/Patient91"
TMP_FOLDER = "tmp"
OUTPUT_FOLDER = "output"


def find_DICOM_groups(main_folder, tmp_folder):
    """
    Returns an array of dicom groups in the main folder
    @param main_folder: root folder
    @return: array of dicom groups
    """

    groups = []
    rec_find_DICOM_groups(main_folder, tmp_folder, groups)
    return groups


def rec_find_DICOM_groups(main_folder, tmp_folder, groups):
    dg = DICOMGroup(dicom_folder=main_folder,
                    group_name=main_folder.split('/')[-1] if "/" in main_folder else main_folder,
                    tmp_folder=tmp_folder)
    if dg.load_folder() is True:
        print("Found Patient #" + str(len(groups) + 1) + ": " + dg.get_name())
        groups.append(dg)
    for subfolder_name in os.listdir(main_folder):
        subfolder_path = main_folder + "/" + subfolder_name
        if os.path.isdir(subfolder_path):
            rec_find_DICOM_groups(subfolder_path, tmp_folder, groups)
    return groups

if __name__ == "__main__":

    # Load configuration parameters
    config = configparser.ConfigParser()
    config.read('../macaron.config')

    # Checking and clearing TMP_FOLDER
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)
    else:
        clear_folder(TMP_FOLDER)

    # Checking OUTPUT_FOLDER
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    if os.path.exists(MAIN_FOLDER) and os.path.isdir(MAIN_FOLDER):

        groups = find_DICOM_groups(MAIN_FOLDER, TMP_FOLDER)

        for group in groups:

            obs = group.get_rtp_objects()
            #DB_Manager.store_all(group, config["database"]["username"], config["database"]["password"], OUTPUT_FOLDER)
            # #
            # # # Getting structures for the patient
            # cm = group.calculate_RTPlan_custom_metrics()
            # structures = group.get_structures()
            # # Getting treatment Plan
            # plan, rt_plan = dg.get_plan()
            # #
            # # Generate DVH
            # dvhs, figure_dvh =  group.generate_DVH()
            # # # Calculating radiomic features
            # radiomic_features = group.calculate_radiomics()
            #dose_radiomics = group.calculate_dose_radiomics()
            # #
            # # # Calculating RTPlan metrics
            # rtp_metrics = group.calculate_RTPlan_metrics(output_folder=OUTPUT_FOLDER)
            group.report(studies=[DICOMStudy.CONTROL_POINT_METRICS], output_folder=OUTPUT_FOLDER)
            print("THE END")

    else:
        print("Folder '" + MAIN_FOLDER + "' does not exist or it is not a folder")