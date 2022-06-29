from enum import Enum


class DICOMStudy(Enum):
    """
    Enum variable that contains all the possible studies from a DICOMGroup
    """
    CONTROL_POINT_METRICS = 8
    STRUCTURES = 1
    PLAN_DETAIL = 2
    RADIOMIC_FEATURES = 3
    PLAN_METRICS_IMG = 4
    PLAN_METRICS_DATA = 5
    DVH_IMG = 6
    DVH_DATA = 7

