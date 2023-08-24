import os.path

import vtk
from SimpleITK import SimpleITK
from radiomics import featureextractor

OBJ_FILE = "..\\DICOM_files\\isodosi\\Patient3\\1.2.826.0.1.63521.232253383772650462411287841667927978288\\patient3_segmentation.nrrd"
MASK_FILE = "..\\DICOM_files\\isodosi\\Patient3\\1.2.826.0.1.63521.232253383772650462411287841667927978288\\IsodoseLevel_80_.vtk"


def stlToJPG(stl_file):
    from stl import mesh
    from mpl_toolkits import mplot3d
    from matplotlib import pyplot

    # Create a new plot
    figure = pyplot.figure()
    axes = mplot3d.Axes3D(figure)

    # Load the STL files and add the vectors to the plot
    your_mesh = mesh.Mesh.from_file('tests/stl_binary/HalfDonut.stl')
    axes.add_collection3d(mplot3d.art3d.Poly3DCollection(your_mesh.vectors))

    # Auto scale to the mesh size
    scale = your_mesh.points.flatten()
    axes.auto_scale_xyz(scale, scale, scale)

    # Show the plot to the screen
    pyplot.show()
    pyplot.savefig("file_name.jpg")


def vtkToNumpy(data):
    temp = vtk.util.numpy_support.vtk_to_numpy(data.GetPointData().GetScalars())
    dims = data.GetDimensions()
    component = data.GetNumberOfScalarComponents()
    if component == 1:
        numpy_data = temp.reshape(dims[2], dims[1], dims[0])
        numpy_data = numpy_data.transpose(2,1,0)
    elif component == 3 or component == 4:
        if dims[2] == 1: # a 2D RGB image
            numpy_data = temp.reshape(dims[1], dims[0], component)
            numpy_data = numpy_data.transpose(0, 1, 2)
            numpy_data = np.flipud(numpy_data)
        else:
            raise RuntimeError('unknow type')
    return numpy_data


if __name__ == "__main__":

    mask_obj = None
    if os.path.exists(MASK_FILE):
        if MASK_FILE.endswith(".vtk"):
            reader = vtk.vtkPolyDataReader()
            reader.SetFileName(MASK_FILE)
            reader.Update()
            data = vtkToNumpy(reader.GetOutput())
            a = 1
        else:
            mask_obj = MASK_FILE

    obj_obj = None
    if os.path.exists(OBJ_FILE):
        obj_obj = OBJ_FILE

    if mask_obj is not None:
        if obj_obj is not None:
            settings = {'binWidth': 100,
                        'resampledPixelSpacing': None,
                        'interpolator': SimpleITK.sitkBSpline}

            # Initialize feature extractor
            extractor = featureextractor.RadiomicsFeatureExtractor(**settings)
            extractor.enableAllFeatures()
            print("Calculating Radiomic IsoDose features for '" + obj_obj + "', structure '" + mask_obj + "'")
            r_f = extractor.execute(obj_obj, mask_obj)
            print(r_f)
        else:
            print("Missing object")
    else:
        print("Missing MASK file")
