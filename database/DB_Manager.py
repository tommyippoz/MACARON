import configparser

import mysql.connector

from MACARON_Utils.DICOM_Study import DICOMStudy
from MACARON_Utils.DICOM_utils import build_DVH_info


def connect(username, password):
    mydb = mysql.connector.connect(
        host="localhost",
        user=username,
        password=password,
        database="macaron")
    return mydb


def call_procedure(mydb, proc_name, params, n_out):
    cursor = mydb.cursor()
    proc_res = cursor.callproc(proc_name, args=params)
    mydb.commit()
    cursor.close()
    return proc_res[-n_out:]


def store_patient(db, dg):
    """
    Stores data of the Patient in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the patient_id
    """
    patient_data = dg.get_patient_info()
    check_id = call_procedure(db, "get_patient", (dg.get_name(), 0), 1)[0]
    if check_id is None:
        params = (dg.get_name(), patient_data["Sex"], patient_data["BirthDate"], patient_data["ID"], 0)
        patient_id = call_procedure(db, "add_patient_full", params, 1)
        return patient_id[0]
    else:
        print("Patient  '" + dg.get_name() + "' already in the DB, not adding it again")
        return check_id


def store_plan(db, dg):
    """
    Stores data of the RTPlan in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the plan_id
    """
    plan_data, pd = dg.get_plan()
    check_id = call_procedure(db, "get_rtplan", (plan_data["label"], plan_data["name"], 0), 1)[0]
    if check_id is None:
        params = (plan_data["label"], plan_data["date"], plan_data["time"],
                  plan_data["name"], plan_data["rxdose"], plan_data["brachy"], 0)
        plan_id = call_procedure(db, "add_rtp_full", params, 1)
        return plan_id[0]
    else:
        print("RTPLan  '" + plan_data["label"] + "' already in the DB, not adding it again")
        return check_id


def store_structures(db, dg):
    """
    Stores data of the structures in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the structure_ids
    """
    structures = dg.get_structures()
    structure_ids = []
    for index in structures:
        structure = structures[index]
        check_id = call_procedure(db, "get_structure_from_name", (structure["name"], 0), 1)[0]
        if check_id is None:
            params = (structure["id"], structure["name"], structure["type"],
                      0 if structure["empty"] is False else 1,
                      structure["color"][0].item(), structure["color"][1].item(),
                      structure["color"][2].item(), 0)
            structure_id = call_procedure(db, "add_structure_full", params, 1)
            structure_ids.append(structure_id[0])
        else:
            print("Structure '" + structure["name"] + "' already in the DB, not adding it again")
            structure_ids.append(check_id)
    return structure_ids


def store_dose(db, dg):
    """
    Stores data of the RTDose in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the dose_id
    """
    dose_data = dg.get_dose_info()
    params = (float(dose_data["GridScaling"]), dose_data["SumType"],
              dose_data["Type"], dose_data["Units"], 0)
    dose_id = call_procedure(db, "add_rtd_full", params, 1)
    return dose_id[0]


def store_group(db, dg, rtp_id, rtd_id, patient_id):
    """
    Stores DICOMGroup data in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the group_id
    """
    check_id = call_procedure(db, "get_group", (dg.get_name(), 0), 1)[0]
    if check_id is None:
        params = (dg.get_name(), rtp_id, rtd_id, patient_id, 0)
        group_id = call_procedure(db, "add_group_from_ids", params, 1)
        new_id = group_id[0]
    else:
        print("DICOM Group already exists, not adding it again")
        new_id = check_id
    return new_id


def store_group_structure(db, group_id, structure_ids):
    """
    Stores group-structure data  in the MySQL database
    @param db: database connection
    @return: the gs_id
    """
    gs_ids = []
    for s_id in structure_ids:
        check_id = call_procedure(db, "get_group_structure", (group_id, s_id, 0), 1)[0]
        if check_id is None:
            params = (group_id, s_id, 0)
            gs_id = call_procedure(db, "add_group_structure", params, 1)
            gs_ids.append(gs_id[0])
        else:
            print("Group-Structure already exists, not adding it again")
            gs_ids.append(check_id)
    return gs_ids


def store_radiomics(db, dg, g_id):
    """
    Stores data of the Radiomic Features in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the radiomic_ids
    """
    radiomics = dg.calculate_radiomics()
    radiomic_ids = []
    for structure in radiomics:
        gs_id = call_procedure(db, "get_structure_id", (g_id, structure, 0), 1)[0]
        for feature_name in radiomics[structure]:
            f_value = str(radiomics[structure][feature_name])
            if len(f_value) < 200:
                params = (gs_id, feature_name, f_value, 0)
                feature_id = call_procedure(db, "add_radiomic_feature", params, 1)
                radiomic_ids.append(feature_id)
            else:
                print(feature_name + " has feature value that exceeds 200 characters")
    return radiomic_ids


def store_plan_metric(db, dg, g_id, img_folder):
    """
    Stores data of the RTPlan  Quality Metrics in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the pc_ids
    """
    p_metrics, p_path = dg.calculate_RTPlan_metrics(output_folder=img_folder)
    pm_ids = []
    for metric in p_metrics:
        params = (g_id, metric, float(p_metrics[metric][0]), p_path[metric], 0)
        pm_id = call_procedure(db, "add_plan_metric_value", params, 1)
        pm_ids.append(pm_id)
    return pm_ids[0]


def store_dvh(db, dg, g_id, img_folder):
    """
    Stores data of the RTPlan  Quality Metrics in the MySQL database
    @param db: database connection
    @param dg: DICOM Group
    @return: the pc_ids
    """
    dvhs, dvh_fig = dg.generate_DVH()
    dvh_img_path = dg.print_dvh(output_folder=img_folder)

    dvh_ids = []
    for structure in dvhs:
        dvh_info = build_DVH_info(dvhs[structure])
        gs_id = call_procedure(db, "get_structure_id", (g_id, dvh_info["Structure"], 0), 1)[0]

        check_id = call_procedure(db, "get_dvh", (gs_id, 0), 1)[0]
        if check_id is None:
            # Add DVH
            params = (gs_id, dvh_img_path, float(dvh_info["abs volume"]), dvh_info["type"], dvh_info["volume unit"],
                      dvh_info["dose unit"], float(dvh_info["Max Dose"]), float(dvh_info["Min Dose"]),
                      float(dvh_info["Mean Dose"]), float(dvh_info["D100"].value), float(dvh_info["D98"].value),
                      float(dvh_info["D95"].value), float(dvh_info["D2cc"].value), 0)
            dvh_id = call_procedure(db, "add_dvh", params, 1)[0]
            dvh_ids.append(dvh_id)

            # Add DVH detail with all data
            counts = [float(x) for x in dvh_info["counts"].split(',')]
            bins = [float(x) for x in dvh_info["bins"].split(',')]
            for i in range(0, len(counts)):
                params = (dvh_id, counts[i], bins[i], 0)
                dvh_detail_id = call_procedure(db, "add_dvh_detail", params, 1)

            print("DVH '" + dvh_info["Structure"] + "' stored in the DB")
        else:
            print("DVH for structure '" + dvh_info["Structure"] + "' already exists, not adding it again")
            dvh_ids.append(check_id)

    return dvh_ids


def create_patient(db, dg):
    """
    Stores all data from a DICOM Group in a database
    """
    patient_id = store_patient(db, dg)
    rtp_id = store_plan(db, dg)
    rtd_id = store_dose(db, dg)
    group_id = store_group(db, dg, rtp_id, rtd_id, patient_id)
    return group_id


def store_all(dg, username, password, img_folder):
    """
    Stores all data from a DICOM Group in a database
    """
    db = connect(username, password)
    patient_id = store_patient(db, dg)
    rtp_id = store_plan(db, dg)
    structures_id = store_structures(db, dg)
    rtd_id = store_dose(db, dg)
    group_id = store_group(db, dg, rtp_id, rtd_id, patient_id)
    gs_ids = store_group_structure(db, group_id, structures_id)
    radiomic_ids = store_radiomics(db, dg, group_id)
    pm_ids = store_plan_metric(db, dg, group_id, img_folder)
    dvh_ids = store_dvh(db, dg, group_id, img_folder)


def store(study, patient, db_conn, group_id, img_folder):
    if study is DICOMStudy.STRUCTURES:
        structures_id = store_structures(db_conn, patient)
        return store_group_structure(db_conn, group_id, structures_id)
    elif study is DICOMStudy.PLAN_DETAIL:
        return
    elif study is DICOMStudy.PLAN_METRICS_DATA or study is DICOMStudy.PLAN_METRICS_IMG:
        return store_plan_metric(db_conn, patient, group_id, img_folder)
    elif study is DICOMStudy.RADIOMIC_FEATURES:
        return store_radiomics(db_conn, patient, group_id)
    elif study is DICOMStudy.DVH_IMG or study is DICOMStudy.DVH_DATA:
        return store_dvh(db_conn, patient, group_id, img_folder)
    else:
        print("Cannot recognize study '" + study + "' to compute and store in DB")


def clean_db(db):
    call_procedure(db, "clean_macaron_db", (None), 1)
    return None


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('../macaron.config')

    db = connect(config["database"]["username"], config["database"]["password"])

    res = call_procedure(db, "add_patient", ("ciaone", 0), 1)
    print(res)
    
    db.close()
