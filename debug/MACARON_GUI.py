import configparser
import os
import tkinter
import tkinter.font
from time import sleep
from tkinter import *
from tkinter import ttk



from tkinter.filedialog import askdirectory

from PIL import Image, ImageTk

from MACARON_Utils.DICOM_Group import DICOMGroup
from MACARON_Utils.DICOM_Study import DICOMStudy
from MACARON_Utils.general_utils import clear_folder
from database import DB_Manager
from database.DB_Manager import connect, create_patient

TMP_FOLDER = "tmp"

OUT_FOLDER = "output"


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


def check_folder(dicom_folder):
    patients = []
    dg = DICOMGroup(dicom_folder=dicom_folder,
                    group_name=dicom_folder.split('/')[-1] if "/" in dicom_folder else dicom_folder,
                    tmp_folder=TMP_FOLDER)
    if dg.load_folder() is True:
        print("Found Patient #" + str(len(patients) + 1) + ": " + dg.get_name())
        patients.append(dg)
    for subfolder_name in os.listdir(dicom_folder):
        subfolder_path = dicom_folder + "/" + subfolder_name
        if os.path.isdir(subfolder_path):
            dg = DICOMGroup(dicom_folder=subfolder_path, group_name=subfolder_name, tmp_folder=TMP_FOLDER)
            if dg.load_folder() is True:
                print("Found Patient #" + str(len(patients) + 1) + ": " + dg.get_name())
                patients.append(dg)
    return patients


class MacaronGUI(tkinter.Frame):

    @classmethod
    def main(cls, config):
        root = Tk()
        root.title('MACARON GUI')
        root.iconbitmap('../resources/MACARON_nobackground.ico')
        root.configure(background='white')
        root.resizable(False, False)
        default_font = tkinter.font.nametofont("TkDefaultFont")
        default_font.configure(size=11)
        cls(root, config)
        root.eval('tk::PlaceWindow . center')
        root.mainloop()

    def __init__(self, root, config):
        super().__init__(root)
        self.checkboxes = [
            ["Structures", BooleanVar(value=True), DICOMStudy.STRUCTURES],
            ["DVH Data", BooleanVar(value=True), DICOMStudy.DVH_DATA],
            ["DVH Plot", BooleanVar(value=True), DICOMStudy.DVH_IMG],
            ["Radiomic Features", BooleanVar(value=True), DICOMStudy.RADIOMIC_FEATURES],
            ["Plan", BooleanVar(value=True), DICOMStudy.PLAN_DETAIL],
            ["Plan Metrics Data", BooleanVar(value=True), DICOMStudy.PLAN_METRICS_DATA],
            ["Plan Metrics Plots", BooleanVar(value=True), DICOMStudy.PLAN_METRICS_IMG],
            ["Control Point Metrics", BooleanVar(value=True), DICOMStudy.CONTROL_POINT_METRICS]]

        # Frame Init
        self.root = root
        self.header = Frame(root, bg="white")
        self.content = Frame(root, bg="white")

        self.dicom_folder = None
        self.group_label = None
        self.run_button = None
        self.patients = []

        self.store_data = None
        self.create_data = None
        self.clean_db = None
        self.clean_data = None

        self.db_user =  config["database"]["username"]
        self.db_psw = config["database"]["password"]

        # Build UI
        self.build_ui()

    def build_ui(self):
        # Grid Setup
        self.header.grid(padx=20, pady=10)
        self.content.grid(padx=20, pady=10)

        # Header
        head_lbl = Label(self.header, text="MACARON: data collection and Machine leArning \n "
                                           "to improve radiomiCs And support Radiation ONcology",
                         font='Helvetica 12 bold', bg="white")
        head_lbl.grid(column=0, row=0, columnspan=2)

        folder_lbl = Label(self.header, text="Select Folder with DICOMs", bg="white")
        folder_lbl.grid(column=0, row=1, padx=10, pady=5)
        folder_button = Button(self.header, text="Browse Folder", command=self.select_folder, bg="white")
        folder_button.grid(column=1, row=1, padx=10, pady=5)

        folder_lbl = Label(self.header, text="Patients Found in Folder:", bg="white")
        folder_lbl.grid(column=0, row=2, padx=10, pady=5)
        self.group_label = Label(self.header, text="---", bg="white")
        self.group_label.grid(column=1, row=2, padx=10, pady=5)

        folder_lbl = Label(self.content, text="MACARON Calculators:", font='Helvetica 12 bold', bg="white")
        folder_lbl.grid(column=0, row=0, columnspan=2, padx=10, pady=10)

        checkboxes = []

        # CheckBoxes for Python Functions
        for [item, variable, tag] in self.checkboxes:
            cb = Checkbutton(self.content, text=item, variable=variable, onvalue=True, bg="white")
            cb.grid(sticky="W", column=0, row=len(checkboxes)+1, padx=10, pady=5)
            checkboxes.append(cb)

        photo = ImageTk.PhotoImage(Image.open('../resources/MACARON.png'))
        label = Label(self.content, image=photo, bg="white")
        label.image = photo
        label.grid(column=1, row=1, rowspan=len(checkboxes), padx=10, pady=5)

        folder_lbl = Label(self.content, text="MACARON Output:", font='Helvetica 12 bold', bg="white")
        folder_lbl.grid(column=0, row=len(checkboxes)+1, columnspan=2, padx=10, pady=10)

        self.store_data = BooleanVar(value=True)
        db_cb = Checkbutton(self.content, text="Store Results in Database",
                                 variable=self.store_data, onvalue=True, bg="white")
        db_cb.grid(column=0, row=len(checkboxes)+2, padx=10, pady=10)

        self.clean_db = BooleanVar(value=False)
        db_clean_cb = Checkbutton(self.content, text="Clean Database",
                            variable=self.clean_db, onvalue=True, bg="white")
        db_clean_cb.grid(column=1, row=len(checkboxes) + 2, padx=10, pady=10)

        self.create_data = BooleanVar(value=True)
        db_cb = Checkbutton(self.content, text="File Output",
                            variable=self.create_data, onvalue=True, bg="white")
        db_cb.grid(column=0, row=len(checkboxes) + 3, padx=10, pady=10)

        self.clean_data = BooleanVar(value=False)
        data_clean_cb = Checkbutton(self.content, text="Clean Files",
                            variable=self.clean_data, onvalue=True, bg="white")
        data_clean_cb.grid(column=1, row=len(checkboxes) + 3, padx=10, pady=10)

        self.run_button = Button(self.content, text="Load DICOM Folder to Run Analysis", bg="white",
                                 command=self.run_analysis, state=DISABLED)
        self.run_button.grid(column=0, row=len(checkboxes)+4, columnspan=2, padx=10, pady=10)


    def select_folder(self):
        folder = askdirectory(initialdir="./")
        if folder is not None:
            self.dicom_folder = folder
            patients = find_DICOM_groups(self.dicom_folder, TMP_FOLDER)
            if patients is not None:
                self.patients = patients
                self.group_label['text'] = str(len(patients))
                self.run_button['text'] = "Process DICOM Data"
                self.run_button['state'] = "normal"
        else:
            print("Not a valid DICOM folder")

    def run_analysis(self):
        self.run_button['state'] = "disabled"
        # start progress bar
        popup = tkinter.Toplevel()
        popup.resizable(False, False)

        Label(popup, text="MACARON Analysis").grid(row=0, column=0)

        progress_var = DoubleVar()
        progress_bar = ttk.Progressbar(popup, variable=progress_var, maximum=100)
        progress_bar.grid(row=1, column=0)
        info_label = Label(popup, text="---")
        info_label.grid(row=2, column=0)

        popup.pack_slaves()

        # Summarize Studies to run
        studies = []
        for [name, var, tag] in self.checkboxes:
            if var.get() is True:
                studies.append([name, tag])

        # Bar Setup
        progress_step = float(100.0 / (len(studies)*len(self.patients)))
        progress = 0

        # Analysis Loop
        if self.clean_data is True:
            clean_folder = True
        else:
            clean_folder = False
        if self.store_data.get() is True:
            db_conn = connect(self.db_user, self.db_psw)
            if self.clean_db is True:
                DB_Manager.clean_db(db_conn)
                print("Dataset was cleared")
        for patient in self.patients:
            study_index = 1
            if self.store_data.get() is True:
                patient_id = create_patient(db_conn, patient)
            for [name, study] in studies:
                popup.update()
                info_label['text'] = "Processing '" + patient.get_name() + "' for study " + \
                                     name + "' [" + str(study_index) + "/" + str(len(studies)) + "]"
                if self.store_data.get() is True:
                    DB_Manager.store(study, patient, db_conn, patient_id, OUT_FOLDER)
                    print("Results of '" + str(study) + "' for patient '" + patient.get_name() + "' were computed and stored in the DB")
                if self.create_data.get() is True:
                    patient.report(studies=[study], output_folder="output", clean_folder=clean_folder)
                    print("Results of '" + str(study) + "' for patient '" + patient.get_name() + "' were computed and stored as TXT/CSV files or Images")
                progress += progress_step
                progress_var.set(progress)
                clean_folder = False
                study_index = study_index + 1

        progress_bar.stop()
        self.run_button['state'] = "normal"
        popup.destroy()


if __name__ == "__main__":

    # Load configuration parameters
    config = configparser.ConfigParser()
    config.read('../macaron.config')

    # Checking and clearing TMP_FOLDER
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)
    else:
        clear_folder(TMP_FOLDER)

    # Checking and clearing OUT_FOLDER
    if not os.path.exists(OUT_FOLDER):
        os.makedirs(OUT_FOLDER)
    else:
        clear_folder(OUT_FOLDER)

    MacaronGUI.main(config)
