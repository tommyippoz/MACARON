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

        for group in groups:

            print("Analyzing Patient " + group.get_name())

            cms = group.calculate_RTPlan_custom_metrics()
            i = 0

            for cm in cms:
                pm = cm["plan"]
                pm["patient"] = group.get_name() + "_" + str(i)
                i = i + 1
                if df is None:
                    df = pandas.DataFrame(columns=list(pm.keys()))
                df = df.append(pm, ignore_index=True)

            # if "/" in group.get_folder():
            #     group_folder = OUTPUT_FOLDER + "/" + group.get_folder().split("/")[-1] + "/"
            # else:
            #     group_folder = OUTPUT_FOLDER + "/" + group.get_folder() + "/"
            # if os.path.exists(group_folder):
            #     print("Deleting existing info inside '" + group_folder + "' folder")
            #     clear_folder(group_folder)
            # else:
            #     os.makedirs(group_folder)
            #
            # for i in range(0, len(cm_list)):
            #     out_file = group_folder + "plan_custom_complexity_metrics_" + str(i) + ".csv"
            #     write_dict(dict_obj=cm_list[i], filename=out_file,
            #                header="beam,attribute,list_index,metric_name,metric_value")

        df.to_csv(OUTPUT_FOLDER + "/foo.csv", index=False)

    else:
        print("Folder '" + MAIN_FOLDER + "' does not exist or it is not a folder")
