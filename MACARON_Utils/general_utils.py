import distutils.spawn
import os
import shutil
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
