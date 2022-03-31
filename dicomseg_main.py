import pydicom
import pydicom_seg
import SimpleITK as sitk
from pydicom_seg import writer

from MACARON_Utils.DICOM_Group import DICOMGroup

MAIN_FOLDER = "./DICOM_files"


if __name__ == "__main__":
    dg = DICOMGroup(MAIN_FOLDER)
    dg.load_folder()

    template = dg.rts_object.dicom_ob
    writer = pydicom_seg.MultiClassWriter(
        template=template,
        inplane_cropping=True,  # Crop image slices to the minimum bounding box on
        # x and y axes
        skip_empty_slices=True,  # Don't encode slices with only zeros
        skip_missing_segment=False,  # If a segment definition is missing in the
        # template, then raise an error instead of
        # skipping it.
    )

    reader = sitk.ImageSeriesReader()
    dcm_files = reader.GetGDCMSeriesFileNames('./DICOM_files')
    reader.SetFileNames(dcm_files)
    image = reader.Execute()
    image_data = sitk.GetArrayFromImage(image)
    segmentation_data = image_data
    segmentation = sitk.GetImageFromArray(segmentation_data)
    segmentation.CopyInformation(image)
    source_images = [
        pydicom.dcmread(x, stop_before_pixels=True, force=True)
        for x in dcm_files
    ]
    #dcm = writer.write(segmentation=segmentation, source_images=source_images)
    dcm = writer.write(segmentation, dcm_files)
    dcm.save_as('segmentation.dcm')



