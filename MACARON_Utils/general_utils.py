import distutils.spawn
import os
import shutil
import numpy
import SimpleITK
from subprocess import call


def clear_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def create_CT_NRRD(ct_folder, nrrd_filename):
    if distutils.spawn.find_executable('plastimatch') is not None:
        call(['plastimatch', 'convert', '--input', ct_folder, '--output-img', nrrd_filename])
    else:
        print("Dependency converter(s) not found in the path.\n Plastimatch (http://plastimatch.org/) "
              "needs to be installed and available in the PATH for using this converter script.")


def create_mask_NRRD(ct_folder, nrrd_filename, rt_struct_filename):
    if distutils.spawn.find_executable('plastimatch') is not None:
        call(['plastimatch', 'convert', '--input', rt_struct_filename, '--output-labelmap', nrrd_filename,
              '--referenced-ct', ct_folder])
    else:
        print("Dependency converter(s) not found in the path.\n Plastimatch (http://plastimatch.org/) "
              "needs to be installed and available in the PATH for using this converter script.")


def create_masks_NRRD(tmp_folder, rt_struct_filename, rt_dose_filename, name, ct_nrrd_filename):
    if distutils.spawn.find_executable('plastimatch') is not None:
        call(['plastimatch', 'convert', '--input', rt_struct_filename, '--output-prefix',
              tmp_folder + "/" + name + '_masks', '--prefix-format', 'nrrd', '--output-ss-list', 'image.txt',
              '--input-dose-img', rt_dose_filename, '--fixed', ct_nrrd_filename])

        # process_mask_NRRD(nrrd_filename)
    else:
        print("Dependency converter(s) not found in the path.\n Plastimatch (http://plastimatch.org/) "
              "needs to be installed and available in the PATH for using this converter script.")


def process_mask_NRRD(mask_NRRD_file):
    ma = SimpleITK.ReadImage(mask_NRRD_file)
    ma_arr = SimpleITK.GetArrayFromImage(ma)

    labels = []
    for channel in range(ma_arr.shape[2]):
        for bit in range(8):
            label_map = numpy.zeros(ma_arr.shape[:2], dtype='uint8')
            roi = numpy.bitwise_and(ma_arr[..., channel], 2 ** bit) > 0
            if numpy.sum(roi) > 0:
                label_map[roi] = 1
                labels.append(label_map)

    mask_arr = numpy.array(labels).transpose(1, 2, 0)
    mask_arr.shape
    mask = SimpleITK.GetImageFromArray(mask_arr)
    mask.CopyInformation(ma)

    SimpleITK.WriteImage(mask, mask_NRRD_file, True)  # Specify True to enable compression