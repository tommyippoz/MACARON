from enum import Enum


class DICOMType(Enum):
    """
    Enum for typings of DCM files
    """
    RT_STRUCT = 1
    RT_PLAN = 2
    RT_DOSE = 3
    TC = 4
    OTHER = 5
