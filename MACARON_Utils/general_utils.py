import distutils.spawn
import os
import shutil
import sys

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


def write_dict(dict_obj, filename, header=None):
    with open(filename, 'w') as f:
        if header is not None:
            f.write("%s\n" % header)
        write_rec_dict(f, dict_obj, "")


def write_rec_dict(out_f, dict_obj, prequel):
    if (type(dict_obj) is dict) or issubclass(type(dict_obj), dict):
        for key in dict_obj.keys():
            if (type(dict_obj[key]) is dict) or issubclass(type(dict_obj[key]), dict):
                if len(dict_obj[key]) > 20:
                    for inner in dict_obj[key].keys():
                        if (prequel is None) or (len(prequel) == 0):
                            out_f.write("%s,%s,%s\n" % (key, inner, dict_obj[key][inner]))
                        else:
                            out_f.write("%s,%s,%s,%s\n" % (prequel, key, inner, dict_obj[key][inner]))
                else:
                    new_prequel = prequel + "," + str(key) if (prequel is not None) and (len(prequel) > 0) else str(key)
                    write_rec_dict(out_f, dict_obj[key], new_prequel)
            elif type(dict_obj[key]) is list:
                item_count = 1
                for item in dict_obj[key]:
                    new_prequel = prequel + "," + str(key) + ",item" + str(item_count) \
                        if (prequel is not None) and (len(prequel) > 0) else str(key) + ",item" + str(item_count)
                    write_rec_dict(out_f, item, new_prequel)
                    item_count += 1
            else:
                if (prequel is None) or (len(prequel) == 0):
                    out_f.write("%s,%s\n" % (key, dict_obj[key]))
                else:
                    out_f.write("%s,%s,%s\n" % (prequel, key, dict_obj[key]))
    else:
        if (prequel is None) or (len(prequel) == 0):
            out_f.write("%s\n" % dict_obj)
        else:
            out_f.write("%s,%s\n" % (prequel, dict_obj))


def test_NRRD(base_file, nrrd_filename, ct_nrrd_filename):
    if distutils.spawn.find_executable('plastimatch') is not None:
        call(['plastimatch', 'convert', '--input', base_file, '--output-dose-img', nrrd_filename,
              '--fixed', ct_nrrd_filename, '--prefix-format', 'nrrd'])
        call(['plastimatch', 'resample', '--input', nrrd_filename, '--output', nrrd_filename,
              '--fixed', ct_nrrd_filename])
    else:
        print("Dependency converter(s) not found in the path.\n Plastimatch (http://plastimatch.org/) "
              "needs to be installed and available in the PATH for using this converter script.")


def create_CT_NRRD(ct_folder, nrrd_filename):
    if distutils.spawn.find_executable('plastimatch') is not None:
        call(['plastimatch', 'convert', '--input', ct_folder, '--output-img', nrrd_filename])
    else:
        print("Dependency converter(s) not found in the path.\n Plastimatch (http://plastimatch.org/) "
              "needs to be installed and available in the PATH for using this converter script.")


def create_mask_NRRD(ct_folder, nrrd_filename, base_filename):
    if distutils.spawn.find_executable('plastimatch') is not None:
        call(['plastimatch', 'convert', '--input', base_filename, '--output-prefix', nrrd_filename,
              '--referenced-ct', ct_folder, '--prefix-format', 'nrrd'])
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


def complexity_indexes(y12, lj_array, jawSize=5):

    minActiveIndex = int(len(lj_array)/4) + int(y12[0] / jawSize)
    maxActiveIndex = int(len(lj_array)/4) + int(y12[1] / jawSize)

    # Pre-Scan of the MLCs
    max_right = -sys.float_info.max
    min_left = sys.float_info.max
    for i in range(minActiveIndex, maxActiveIndex):
        # Computing Aperture
        left = lj_array[i]
        right = lj_array[int(len(lj_array) / 2) + i]
        # Finding minleft / maxright
        if left < min_left:
            min_left = left
        if right > max_right:
            max_right = right
    pos_max =  abs(max_right - min_left)

    # Computing most of the Metrics
    apertures = []
    left_old = 0
    right_old = 0
    lsv_l = 0
    lsv_r = 0
    perimeter = 0

    for i in range(minActiveIndex, maxActiveIndex):
        # Computing Aperture
        left = lj_array[i]
        right = lj_array[int(len(lj_array)/2)+i]
        apertures.append(abs(left - right))
        # Computing LSV iteratively
        if i < maxActiveIndex - 1:
            lsv_l = lsv_l + (pos_max - abs(left - lj_array[i+1]))
            lsv_r = lsv_r + (pos_max - abs(right - lj_array[int(len(lj_array)/2)+i+1]))
        # Computing Perimeter iteratively
        ap_i = i - minActiveIndex
        if i == minActiveIndex:
            perimeter += apertures[ap_i]
        else:
            if (right <= left_old) or (left >= right_old):
                # Two apertures do not overlap
                contrib = apertures[ap_i] + apertures[ap_i-1]
            elif (right <= right_old) and (left >= left_old):
                # Old aperture wraps the new one
                contrib = apertures[ap_i-1] - apertures[ap_i]
            elif (right > right_old) and (left < left_old):
                # New aperture wraps the old one
                contrib = apertures[ap_i] - apertures[ap_i-1]
            else:
                # New aperture overlaps + exceeds on the right/left
                contrib = abs(left - left_old) + abs(right - right_old)
            perimeter += contrib
        left_old = left
        right_old = right

    # Finalizing Perimeter
    perimeter += apertures[-1]

    # Finalizing LSV
    lsv = lsv_l*lsv_r/pow(len(apertures)*pos_max, 2)

    # Computing sum of all apertures (active and non active)
    ap_sum = 0
    for i in range(0, int(len(lj_array)/2)):
        left = lj_array[i]
        right = lj_array[int(len(lj_array)/2)+i]
        ap_sum = ap_sum + abs(right - left)

    cm = {
        # Minimum Aperture between aligned MLC
        "minAperture": min(apertures),
        # Maximum Aperture between aligned MLC
        "maxAperture": max(apertures),
        # Maximum Aperture between misaligned MLC
        "maxApertureNoAlign": pos_max,
        # Average Aperture between Active aligned MLCs
        "avgAperture": sum(apertures)/len(apertures),
        # Sum of all apertures (active and non active)
        "sumAllApertures": ap_sum,
        # Size of the window containing active MLCs
        "yDiff": abs(y12[0] - y12[1]),
        # Number of MLCs
        "totalMLC": int(len(lj_array)/2),
        # Number of Active MLCs
        "activeMLC": len(apertures),
        # Active MLC with the lowest index
        "lowestActiveMLC": minActiveIndex,
        # Active MLC with the highest index
        "highestActiveMLC": maxActiveIndex-1,
        # Perimeter of the area exposed to the beam
        "perimeter": perimeter + abs(y12[0] - y12[1])*2,
        # Perimeter of the area exposed to the beam without accounting for MLC thickness
        "perimeterNoMLCSize": perimeter,
        # Area of the area exposed to the beam
        "area": sum(apertures)*jawSize,
        # LSV metric
        "LSV": lsv,
        # Active MLCs which are opened
        "nAperturesG0": sum(ap > 0 for ap in apertures),
        # Active MLCs with aperture lower equal than 2
        "nAperturesLeq2": sum(ap <= 2 for ap in apertures),
        # Active MLCs with aperture lower equal than 5
        "nAperturesLeq5": sum(ap <= 5 for ap in apertures),
        # Active MLCs with aperture lower equal than 10
        "nAperturesLeq10": sum(ap <= 10 for ap in apertures),
        # Active MLCs with aperture lower equal than 20
        "nAperturesLeq20": sum(ap <= 20 for ap in apertures),
        }

    # Complexity measures, left jaws, right jaws
    return cm,  lj_array[0:int(len(lj_array)/2)], lj_array[int(len(lj_array)/2):]
