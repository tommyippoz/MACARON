import configparser
import os.path

import numpy
import pandas

from MACARON_Utils.DICOM_Group import DICOMGroup
from MACARON_Utils.DICOM_Study import DICOMStudy
from MACARON_Utils.general_utils import clear_folder, write_dict

from database import DB_Manager

MAIN_FOLDER = "../DICOM_Files/DicomAnonymized_RED"
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
        df = None
        apertures = {}

        # Iterate over patients
        for group in groups:

            print("Analyzing Patient " + group.get_name())

            cms = group.calculate_RTPlan_custom_metrics()
            i = 0

            # Iterate Over RTPlans for Patients
            for cm in cms:

                # Plan Metrics Summary
                pm = cm["plan"]
                pm["patient"] = group.get_name() + "_" + str(i)
                i = i + 1
                if df is None:
                    df = pandas.DataFrame(columns=list(pm.keys()))
                df = df.append(pm, ignore_index=True)

                # Aperture Summary
                aperture_dict = {"avgApertures": [], "yDiff": []}
                for item in cm.keys():
                    if item is not "plan":
                        seq = cm[item]["Sequence"]
                        for cp in seq:
                            aperture_dict["avgApertures"].append(cp["avgAperture"])
                            aperture_dict["yDiff"].append(cp["yDiff"])
                apertures[pm["patient"]] = aperture_dict

        # Prints Summary of Plan Metrics
        df.to_csv(OUTPUT_FOLDER + "/plan_metrics_summary.csv", index=False)

        # Prints lists of avgApertures and yDiff
        write_dict(apertures, OUTPUT_FOLDER + "/apertures.csv", header="patient,metric,value")

    else:
        print("Folder '" + MAIN_FOLDER + "' does not exist or it is not a folder")
