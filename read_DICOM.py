import pydicom
from matplotlib import pylab

#ds = pydicom.read_file("DICOM_Files/ADAM_staticoDIAM_Dose.dcm", force=True)
#ds = pydicom.read_file("DICOM_Files/ADAM_CT11_image00000.DCM", force=True)
ds = pydicom.read_file("DICOM_Files/ADAM_StrctrSets.dcm", force=True)

pixel_bytes = ds.PixelData

##CT values form a matrix
pix = ds.pixel_array

##Read display image
pylab.imshow(ds.pixel_array, cmap=pylab.cm.bone)
pylab.show()
