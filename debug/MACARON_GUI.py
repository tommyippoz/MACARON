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

TMP_FOLDER = "tmp"

OUT_FOLDER = "output"


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
    def main(cls):
        root = Tk()
        root.title('MACARON GUI')
        root.iconbitmap('../resources/MACARON_nobackground.ico')
        root.configure(background='white')
        root.resizable(False, False)
        default_font = tkinter.font.nametofont("TkDefaultFont")
        default_font.configure(size=11)
        cls(root)
        root.eval('tk::PlaceWindow . center')
        root.mainloop()

    def __init__(self, root):
        super().__init__(root)
        self.checkboxes = [
            ["Structures", BooleanVar(value=True), DICOMStudy.STRUCTURES],
            ["DVH Data", BooleanVar(value=True), DICOMStudy.DVH_DATA],
            ["DVH Plot", BooleanVar(value=True), DICOMStudy.DVH_IMG],
            ["Radiomic Features", BooleanVar(value=True), DICOMStudy.RADIOMIC_FEATURES],
            ["Plan", BooleanVar(value=True), DICOMStudy.PLAN_DETAIL],
            ["Plan Metrics Data", BooleanVar(value=True), DICOMStudy.PLAN_METRICS_DATA],
            ["Plan Metrics Plots", BooleanVar(value=True), DICOMStudy.PLAN_METRICS_IMG]]
        # Frame Init
        self.root = root
        self.header = Frame(root, bg="white")
        self.content = Frame(root, bg="white")

        self.dicom_folder = None
        self.group_label = None
        self.run_button = None
        self.patients = []

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

        self.run_button = Button(self.content, text="Load DICOM Folder to Run Analysis", bg="white",
                                 command=self.run_analysis, state=DISABLED)
        self.run_button.grid(column=0, row=len(checkboxes)+1, columnspan=2, padx=10, pady=10)


    def select_folder(self):
        folder = askdirectory(initialdir="./")
        if folder is not None:
            self.dicom_folder = folder
            patients = check_folder(self.dicom_folder)
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
        progress_bar.grid(row=1, column=0)  # .pack(fill=tk.X, expand=1, side=tk.BOTTOM)
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
        clean_folder = True
        for patient in self.patients:
            study_index = 1
            for [name, study] in studies:
                popup.update()
                info_label['text'] = "Processing '" + patient.get_name() + "' for study " + \
                                     name + "' [" + str(study_index) + "/" + str(len(studies)) + "]"
                patient.report(studies=[study], output_folder="output", clean_folder=clean_folder)
                progress += progress_step
                progress_var.set(progress)
                clean_folder = False
                study_index = study_index + 1

        progress_bar.stop()
        self.run_button['state'] = "normal"
        popup.destroy()


if __name__ == "__main__":
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

    MacaronGUI.main()
