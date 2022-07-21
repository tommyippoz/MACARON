/* 
--------------------------------------------------------------------------------------------------
								    CREATE DATABASE
--------------------------------------------------------------------------------------------------
*/
create database if not exists macaron;
use macaron;

/*
--------------------------------------------------------------------------------------------------
								CLEARING TABLES
--------------------------------------------------------------------------------------------------
*/

drop table if exists GroupControlPointMetric;
drop table if exists ControlPointMetric;
drop table if exists GroupPlanMetric;
drop table if exists PlanMetric;
drop table if exists DVHDetail;
drop table if exists DVH;
drop table if exists StructureFeature;
drop table if exists RadiomicFeature;
drop table if exists FeatureCategory;
drop table if exists GroupStructure;
drop table if exists DicomGroup;
drop table if exists Structure;
drop table if exists RTDose;
drop table if exists RTPlan;
drop table if exists Patient;


/*
--------------------------------------------------------------------------------------------------
								CREATION OF TABLES
--------------------------------------------------------------------------------------------------
*/

create table Patient (
	patient_id int unsigned auto_increment,
    anonymization_detail varchar(200) default null,
    sex char(1) default 'M',
    birthdate date default null,
    dicom_patient_id char(100),
    primary key (patient_id)
);

create table RTPlan (
	rtp_id int unsigned auto_increment,
    plan_label varchar(200) not null,
    plan_date date not null,
    plan_time int unsigned default 0,
    plan_name varchar(300) not null,
    plan_rxdose int unsigned not null,
    plan_brachy bool default false,
    primary key (rtp_id)
);

create table RTDose (
	rtd_id int unsigned auto_increment,
	dose_scaling float not null,
    dose_sum char(20) default "PLAN" not null,
    dose_type char(30) default "PHYSICAL" not null,
	dose_units char(10) default "GY" not null, 
    primary key (rtd_id)
);

create table Structure (
	structure_id int unsigned auto_increment,
    id_number int unsigned not null,
    full_name varchar(200) not null,
    structure_type char(20) default "ORGAN",
    empty_flag smallint default 0,
    color_R int default 0,
    color_G int default 0,
    color_B int default 0,
    primary key (structure_id)
);

create table DicomGroup (
	group_id int unsigned auto_increment,
    group_name varchar(200) default null,
    group_rtp int unsigned,
    group_rtd int unsigned,
    patient_id int unsigned not null,
    primary key (group_id),
    foreign key (patient_id) references Patient(patient_id),
    foreign key (group_rtp) references RTPlan(rtp_id)
);

create table GroupStructure (
	group_structure_id int unsigned auto_increment,
    group_id int unsigned not null,
    structure_id int unsigned not null,
    primary key (group_structure_id),
    foreign key (group_id) references DicomGroup(group_id),
    foreign key (structure_id) references Structure(structure_id)    
);

create table FeatureCategory (
	category_id int unsigned auto_increment,
    category_name varchar(100) not null,
    primary key (category_id)
);

create table RadiomicFeature (
	feature_id int unsigned auto_increment,
	feature_name varchar(200) not null,
    feature_category int unsigned not null,
    feature_type enum("float", "int", "string", "array") default "float",
    primary key (feature_id),
    foreign key (feature_category) references FeatureCategory(category_id)
);

create table StructureFeature (
	structure_feature_id int unsigned auto_increment,
    feature_id int unsigned not null,
    group_structure_id int unsigned not null,
    feature_value varchar(200) not null,
    primary key (structure_feature_id),
    foreign key (group_structure_id) references GroupStructure(group_structure_id),
    foreign key (feature_id) references RadiomicFeature(feature_id)
);

create table DVH (
	dvh_id int unsigned auto_increment,
    group_structure_id int unsigned not null,
    image_path varchar(1024) not null default "./",
    abs_volume int default 0,
    diagram_type enum("cumulative", "relative") default "cumulative",
    volume_unit char(10) default "cm3",
    dose_unit char(10) default "Gy",
    max_dose int,
    min_dose int,
    mean_dose float,
    D100 float default 0,
    D98 float default 0,
    D95 float default 0,
    D2cc float default 0,
    primary key (dvh_id),
    foreign key (group_structure_id) references Structure(structure_id)
);

create table DVHDetail (
	dvh_detail_id int unsigned auto_increment,
    dvh_id int unsigned not null,
    counts float not null,
    bins float not null,
    primary key (dvh_detail_id),
	foreign key (dvh_id) references DVH(dvh_id)
);

create table PlanMetric (
	plan_metric_id int unsigned auto_increment,
    metric_name varchar(100) not null,
    metric_unit varchar(100) default "dimensionless",
    primary key (plan_metric_id)
);

create table GroupPlanMetric (
	group_plan_metric_id int unsigned auto_increment,
    group_id int unsigned not null,
    plan_metric_id int unsigned not null,
    plan_metric_value float not null,
    plan_metric_img varchar(1024) not null,
    primary key (group_plan_metric_id),
    foreign key (group_id) references DicomGroup(group_id),
    foreign key (plan_metric_id) references PlanMetric(plan_metric_id)
);

create table ControlPointMetric (
	cp_metric_id int unsigned auto_increment,
    metric_name varchar(100) not null,
    metric_unit varchar(100) default "cm",
    primary key (cp_metric_id)
);

create table GroupControlPointMetric (
	gcp_metric_id int unsigned auto_increment,
    group_id int unsigned not null,
    cp_index int unsigned not null,
    beam varchar(30) not null,
    cp_metric_id int unsigned not null,
    cp_metric_value float not null,
    primary key (gcp_metric_id),
    foreign key (group_id) references DicomGroup(group_id),
    foreign key (cp_metric_id) references ControlPointMetric(cp_metric_id),
    unique (group_id, cp_index, beam, cp_metric_id)
);



/*
--------------------------------------------------------------------------------------------------
								POPULATING TABLES
--------------------------------------------------------------------------------------------------
*/

DELIMITER //

DROP PROCEDURE IF EXISTS populate_db //
CREATE PROCEDURE populate_db()
BEGIN
	insert into FeatureCategory (category_name) values 
		("diagnostics"), 
		("shape"), 
		("firstorder"), 
		("glcm"),
		("gldm"),
		("glrlm"),
		("glszm"),
		("ngtdm");

	insert into PlanMetric (metric_name, metric_unit) values
		("PyComplexityMetric", "CI [mm^-1]"),
		("MeanAreaMetricEstimator", "mm^2"),
		("AreaMetricEstimator", "mm^2"),
		("ApertureIrregularityMetric", "dimensionless"),
        ("AverageAperture Less1CM", "cm"),
        ("Y1-Y2 Difference Less1CM", "cm");
        
	insert into ControlPointMetric (metric_name, metric_unit) values
		("minAperture", "cm"),
		("maxAperture", "cm"),
		("avgAperture", "cm"),
		("yDiff", "cm"),
        ("totalMLC", "cm"),
        ("activeMLC", "cm"),
        ("lowestActiveMLC", "cm"),
        ("highestActiveMLC", "cm"),
        ("perimeter", "cm"),
        ("perimeterNoMLCSize", "cm"),
        ("area", "cm^2");
		
	/* Diagnostic Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("diagnostics_Versions_PyRadiomics", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Versions_Numpy", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Versions_SimpleITK", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Versions_PyWavelet", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Versions_Python", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Configuration_Settings", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Configuration_EnabledImageTypes", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Image-original_Hash", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Image-original_Dimensionality", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Image-original_Spacing", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Image-original_Size", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Image-original_Mean", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Image-original_Minimum", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Image-original_Maximum", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Mask-original_Hash", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Mask-original_Spacing", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Mask-original_Size", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Mask-original_BoundingBox", (select category_id from FeatureCategory where category_name = "diagnostics"), "string"),
		("diagnostics_Mask-original_VoxelNum", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Mask-original_VolumeNum", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Mask-original_CenterOfMassIndex", (select category_id from FeatureCategory where category_name = "diagnostics"), "float"),
		("diagnostics_Mask-original_CenterOfMass", (select category_id from FeatureCategory where category_name = "diagnostics"), "float");

	/* Shape Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("original_shape_Elongation", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_Flatness", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_LeastAxisLength", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_MajorAxisLength", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_Maximum2DDiameterColumn", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_Maximum2DDiameterRow", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_Maximum2DDiameterSlice", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_Maximum3DDiameter", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_MeshVolume", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_MinorAxisLength", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_Sphericity", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_SurfaceArea", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_SurfaceVolumeRatio", (select category_id from FeatureCategory where category_name = "shape"), "float"),
		("original_shape_VoxelVolume", (select category_id from FeatureCategory where category_name = "shape"), "float");
		
	/* FirstOrder Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("original_firstorder_10Percentile", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_90Percentile", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Energy", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Entropy", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_InterquartileRange", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Kurtosis", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Maximum", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_MeanAbsoluteDeviation", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Mean", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Median", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Minimum", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Range", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_RobustMeanAbsoluteDeviation", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_RootMeanSquared", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Skewness", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_TotalEnergy", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Uniformity", (select category_id from FeatureCategory where category_name = "firstorder"), "float"),
		("original_firstorder_Variance", (select category_id from FeatureCategory where category_name = "firstorder"), "float");

	/* glcm Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("original_glcm_Autocorrelation", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_ClusterProminence", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_ClusterShade", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_ClusterTendency", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Contrast", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Correlation", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_DifferenceAverage", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_DifferenceEntropy", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_DifferenceVariance", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Id", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Idm", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Idmn", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Idn", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Imc1", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_Imc2", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_InverseVariance", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_JointAverage", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_JointEnergy", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_JointEntropy", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_MCC", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_MaximumProbability", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_SumAverage", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_SumEntropy", (select category_id from FeatureCategory where category_name = "glcm"), "float"),
		("original_glcm_SumSquares", (select category_id from FeatureCategory where category_name = "glcm"), "float");

	/* gldm Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("original_gldm_DependenceEntropy", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_DependenceNonUniformity", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_DependenceNonUniformityNormalized", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_DependenceVariance", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_GrayLevelNonUniformity", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_GrayLevelVariance", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_HighGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_LargeDependenceEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_LargeDependenceHighGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_LargeDependenceLowGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_LowGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_SmallDependenceEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_SmallDependenceHighGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float"),
		("original_gldm_SmallDependenceLowGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "gldm"), "float");

	/* glrlm Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("original_glrlm_GrayLevelNonUniformity", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_GrayLevelNonUniformityNormalized", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_GrayLevelVariance", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_HighGrayLevelRunEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_LongRunEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_LongRunHighGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_LongRunLowGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_LowGrayLevelRunEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_RunEntropy", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_RunLengthNonUniformity", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_RunLengthNonUniformityNormalized", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_RunPercentage", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_RunVariance", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_ShortRunEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_ShortRunHighGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float"),
		("original_glrlm_ShortRunLowGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glrlm"), "float");

	/* glszm Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("original_glszm_GrayLevelNonUniformity", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_GrayLevelNonUniformityNormalized", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_GrayLevelVariance", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_HighGrayLevelZoneEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_LargeAreaEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_LargeAreaHighGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_LargeAreaLowGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_LowGrayLevelZoneEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_SizeZoneNonUniformity", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_SizeZoneNonUniformityNormalized", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_SmallAreaEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_SmallAreaHighGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_SmallAreaLowGrayLevelEmphasis", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_ZoneEntropy", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_ZonePercentage", (select category_id from FeatureCategory where category_name = "glszm"), "float"),
		("original_glszm_ZoneVariance", (select category_id from FeatureCategory where category_name = "glszm"), "float");

	/* ngtdm Features */
	insert into RadiomicFeature (feature_name, feature_category, feature_type) values
		("original_ngtdm_Busyness", (select category_id from FeatureCategory where category_name = "ngtdm"), "float"),
		("original_ngtdm_Coarseness", (select category_id from FeatureCategory where category_name = "ngtdm"), "float"),
		("original_ngtdm_Complexity", (select category_id from FeatureCategory where category_name = "ngtdm"), "float"),
		("original_ngtdm_Contrast", (select category_id from FeatureCategory where category_name = "ngtdm"), "float"),
		("original_ngtdm_Strength", (select category_id from FeatureCategory where category_name = "ngtdm"), "float");
		
END //
    
/*
--------------------------------------------------------------------------------------------------
								STORED PROCEDURES
--------------------------------------------------------------------------------------------------
*/


/* Procedure to add a new patient, returnd the patient_id */
DROP PROCEDURE IF EXISTS add_patient_full //
CREATE PROCEDURE add_patient_full (
	IN detail VARCHAR(200),
	IN sex char(1),
    IN birthday date,
    IN dicomID char(100),
    OUT newID int unsigned)
BEGIN
	INSERT INTO Patient (anonymization_detail, sex, birthdate, dicom_patient_id)
		VALUES (detail, sex, birthday, dicomID);
	SET newID = last_insert_id();
END //

/* Procedure to add a new patient, returnd the patient_id */
DROP PROCEDURE IF EXISTS add_patient //
CREATE PROCEDURE add_patient (
	IN detail VARCHAR(200),
    OUT newID int unsigned)
BEGIN
	INSERT INTO Patient (anonymization_detail)
		VALUES (detail);
	SET newID = last_insert_id();
END //

/* Procedure to add a new rtp, returns the rtp_id */
DROP PROCEDURE IF EXISTS add_rtp_full //
CREATE PROCEDURE add_rtp_full (
	IN label VARCHAR(200),
	IN p_date date,
    IN p_time int unsigned,
    IN p_name VARCHAR(300),
    IN rx_dose int unsigned,
    IN brachy bool,
    OUT newID int unsigned)
BEGIN
	INSERT INTO RTPlan (plan_label, plan_date, plan_time, plan_name, plan_rxdose, plan_brachy)
		VALUES (label, p_date, p_time, p_name, rx_dose, brachy);
	SET newID = last_insert_id();
END //

/* Procedure to add a new rtp, returns the rtp_id */
DROP PROCEDURE IF EXISTS add_rtp //
CREATE PROCEDURE add_rtp (
	IN label VARCHAR(200),
	IN p_date date,
    IN p_name VARCHAR(300),
    IN rx_dose int unsigned,
    OUT newID int unsigned)
BEGIN
	INSERT INTO RTPlan (plan_label, plan_date, plan_name, plan_rxdose)
		VALUES (label, p_date, p_name, rx_dose);
	SET newID = last_insert_id();
END //

/* Procedure to add a new structure, returns the structure_id */
DROP PROCEDURE IF EXISTS add_structure_full //
CREATE PROCEDURE add_structure_full (
	IN str_index int unsigned,
	IN str_name VARCHAR(200),
    IN str_type char(20), 
    IN str_flag smallint,
    IN col_R int,
    IN col_G int,
    IN col_B int,
    OUT newID int unsigned)
BEGIN
	INSERT INTO Structure (id_number, full_name, structure_type, empty_flag, color_R, color_G, color_B)
		VALUES (str_index, str_name, str_type, str_flag, col_R, col_G, col_B);
	SET newID = last_insert_id();
END //

/* Procedure to add a new structure, returns the structure_id */
DROP PROCEDURE IF EXISTS add_structure //
CREATE PROCEDURE add_structure (
	IN str_index int unsigned,
	IN str_name VARCHAR(200),
    OUT newID int unsigned)
BEGIN
	INSERT INTO Structure (id_number, full_name)
		VALUES (str_index, str_name);
	SET newID = last_insert_id();
END //

/* Procedure to add a new rt_dose, returns the rtd_id */
DROP PROCEDURE IF EXISTS add_rtd_full //
CREATE PROCEDURE add_rtd_full (
	IN d_scaling float,
    IN d_sum char(20),
    IN d_type char(30),
    IN d_units char(10),
    OUT newID int unsigned)
BEGIN
	INSERT INTO RTDose(dose_scaling, dose_sum, dose_type, dose_units)
		VALUES (d_scaling, d_sum, d_type, d_units);
	SET newID = last_insert_id();
END //

/* Procedure to add a new rt_dose, returns the rtd_id */
DROP PROCEDURE IF EXISTS add_rtd //
CREATE PROCEDURE add_rtd (
	IN d_scaling float,
    OUT newID int unsigned)
BEGIN
	INSERT INTO RTDose(dose_scaling)
		VALUES (d_scaling);
	SET newID = last_insert_id();
END //

/* Procedure to add a new group, returns the group_id */
DROP PROCEDURE IF EXISTS add_group_from_ids //
CREATE PROCEDURE add_group_from_ids (
	IN g_name VARCHAR(200),
    IN rtplan int unsigned,
    IN rtdose int unsigned,
    IN patient int unsigned,
    OUT newID int unsigned)
BEGIN
	INSERT INTO DicomGroup (group_name, group_rtp, group_rtd, patient_id)
		VALUES (g_name, rtplan, rtdose, patient);
	SET newID = last_insert_id();
END //

/* Procedure to add a new group, returns the group_id */
DROP PROCEDURE IF EXISTS add_group //
CREATE PROCEDURE add_group (
	IN pat_detail VARCHAR(200),
	IN g_name VARCHAR(200),
    IN p_label VARCHAR(200),
	IN p_date date,
    IN p_name VARCHAR(300),
    IN p_rxdose int unsigned,
    IN dose_scaling float,
    OUT newID int unsigned)
BEGIN
	CALL add_patient(pat_detail, @patient);
    CALL add_rtd(dose_scaling, @rtdose);
    CALL add_rtp(p_label, p_date, p_name, p_rxdose, @rtplan);
	INSERT INTO DicomGroup (group_name, group_rtp, group_rtd, patient_id)
		VALUES (g_name, @rtplan, @rtdose, @patient);
	SET newID = last_insert_id();
END //

/* Procedure to add a new rt_dose, returns the rtd_id */
DROP PROCEDURE IF EXISTS add_group_structure //
CREATE PROCEDURE add_group_structure(
	IN g_id int unsigned,
    IN s_id int unsigned,
    OUT newID int unsigned)
BEGIN
	INSERT INTO GroupStructure(group_id, structure_id)
		VALUES (g_id, s_id);
	SET newID = last_insert_id();
END //

/* Procedure to add the value of a radiomic feature for a given group, returns the structure_feature_id */
DROP PROCEDURE IF EXISTS add_radiomic_feature //
CREATE PROCEDURE add_radiomic_feature(
	IN gs_id int unsigned,
    IN f_name varchar(200),
    IN f_value varchar(200),
    OUT newID int unsigned)
BEGIN
	DECLARE f_id int unsigned;
    SELECT feature_id
    FROM RadiomicFeature
    WHERE feature_name = f_name
    INTO f_id;
	
    INSERT INTO StructureFeature(feature_id, group_structure_id, feature_value)
		VALUES (f_id, gs_id, f_value);
	SET newID = last_insert_id();
END //

/* Procedure to add a new plan complexity metric value, returns the plan_metric_id */
DROP PROCEDURE IF EXISTS add_plan_metric_value //
CREATE PROCEDURE add_plan_metric_value(
	IN g_id int unsigned,
    IN m_name varchar(100),
    IN pm_value float,
    IN pm_img varchar(1024),
    OUT newID int unsigned)
BEGIN
	DECLARE m_id int unsigned;
    
    SELECT plan_metric_id
    FROM PlanMetric
    WHERE metric_name = m_name
    INTO m_id;

	INSERT INTO GroupPlanMetric(group_id, plan_metric_id, plan_metric_value, plan_metric_img)
		VALUES (g_id, m_id, pm_value, pm_img);
	SET newID = last_insert_id();
END //

/* Procedure to add a new control point metric value, returns the cpm_id */
DROP PROCEDURE IF EXISTS add_control_point_metric_value //
CREATE PROCEDURE add_control_point_metric_value(
	IN g_id int unsigned,
    IN cpm_beam varchar(30),
    IN cpm_name varchar(100),
    IN cpm_value float,
    IN cpm_index int unsigned,
    OUT newID int unsigned)
BEGIN
	DECLARE cpm_id int unsigned;
    
    SELECT cp_metric_id
    FROM ControlPointMetric
    WHERE metric_name = cpm_name
    INTO cpm_id;

	INSERT INTO GroupControlPointMetric(group_id, cp_index, beam, cp_metric_id, cp_metric_value)
		VALUES (g_id, cpm_index, cpm_beam, cpm_id, cpm_value);
	SET newID = last_insert_id();
END //

/* Procedure to add a new control point metric values, returns the cpm_ids */
DROP PROCEDURE IF EXISTS add_control_point_metric_values //
CREATE PROCEDURE add_control_point_metric_values(
	IN g_id int unsigned,
    IN cpm_index int unsigned,
    IN cpm_beam varchar(30),
    IN cpm_min_aperture float,
    IN cpm_max_aperture float,
    IN cpm_avg_aperture float,
    IN cpm_y_diff float,
    IN cpm_tot_jaws float,
    IN cpm_active_jaws float,
    IN cpm_lowest_jaw float,
    IN cpm_highest_jaw float,
    IN cpm_perimeter float,
    IN cpm_perimeter_nojaw float,
    IN cpm_area float,
    OUT newIDS varchar(300))
BEGIN
	DECLARE newIDS varchar(300);
    DECLARE newID int unsigned;
    SET newIDS = "";
    
    CALL add_control_point_metric_value(g_id, cpm_beam, "minAperture", cpm_min_aperture, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "maxAperture", cpm_min_aperture, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "avgAperture", cpm_min_aperture, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "yDiff", cpm_y_diff, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "totalMLC", cpm_tot_jaws, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "activeMLC", cpm_active_jaws, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "lowestActiveMLC", cpm_lowest_jaw, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "highestActiveMLC", cpm_highest_jaw, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "perimeter", cpm_perimeter, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "perimeterNoMLCSize", cpm_perimeter_nojaw, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");
    CALL add_control_point_metric_value(g_id, cpm_beam, "area", cpm_area, cpm_index, @newID);
    SET newIDS = CONCAT(newIDS, CAST(@newID as CHAR(10)), ",");    
    
END //

/* Procedure to add a new dvh, returns the dvh_id */
DROP PROCEDURE IF EXISTS add_dvh //
CREATE PROCEDURE add_dvh(
	IN gs_id int unsigned,
    IN p_image_path varchar(1024),
    IN p_abs_volume int,
    IN p_diagram_type enum("cumulative", "relative"),
    IN p_volume_unit char(10),
    IN p_dose_unit char(10),
    IN p_max_dose int,
    IN p_min_dose int,
    IN p_mean_dose float,
    IN p_D100 float,
    IN p_D98 float,
    IN p_D95 float,
    IN p_D2cc float,
    OUT newID int unsigned)
BEGIN
	INSERT INTO DVH(group_structure_id, image_path, abs_volume, diagram_type, volume_unit, dose_unit, max_dose, 
						min_dose, mean_dose, D100, D98, D95, D2cc)
		VALUES (gs_id, p_image_path, p_abs_volume, p_diagram_type, p_volume_unit, p_dose_unit, p_max_dose, p_min_dose, 
					p_mean_dose, p_D100, p_D98, p_D95, p_D2cc);
	SET newID = last_insert_id();
END //

/* Procedure to add a new dvh detail, returns the dvh_detail_id */
DROP PROCEDURE IF EXISTS add_dvh_detail //
CREATE PROCEDURE add_dvh_detail(
	IN d_id int unsigned,
    IN count float,
    IN bin float,
    OUT newID int unsigned)
BEGIN
	INSERT INTO DVHDetail(dvh_id, counts, bins)
		VALUES (d_id, count, bin);
	SET newID = last_insert_id();
END //



/* Getters Procedures */

/* Procedure to get a structure_id */
DROP PROCEDURE IF EXISTS get_structure_id //
CREATE PROCEDURE get_structure_id(
	IN g_id int unsigned,
    IN s_name varchar(200),
    OUT ID int unsigned)
BEGIN
	SELECT GroupStructure.group_structure_id 
    FROM GroupStructure inner join Structure on GroupStructure.structure_id = Structure.structure_id 
    WHERE Structure.full_name = s_name and GroupStructure.group_id = g_id
    INTO ID;
END //

/* Procedure to get a structure_id */
DROP PROCEDURE IF EXISTS get_structure_from_name //
CREATE PROCEDURE get_structure_from_name(
	IN s_name varchar(200),
    OUT ID int unsigned)
BEGIN
	SELECT structure_id 
    FROM Structure 
    WHERE full_name = s_name
    INTO ID;
END //

/* Procedure to get a group_id */
DROP PROCEDURE IF EXISTS get_group //
CREATE PROCEDURE get_group (
    IN g_name varchar(200),
    OUT newID int unsigned)
BEGIN
	select group_id
    from DicomGroup
    where group_name = g_name
    limit 1
	into newID;
END //


DROP PROCEDURE IF EXISTS get_group_structure //
CREATE PROCEDURE get_group_structure (
    IN g_id int unsigned,
    IN s_id int unsigned,
    OUT newID int unsigned)
BEGIN
	select group_structure_id
    from GroupStructure
    where group_id = g_id and structure_id = s_id
    limit 1
	into newID;
END //


DROP PROCEDURE IF EXISTS get_rtplan //
CREATE PROCEDURE get_rtplan (
    IN p_label varchar(200),
    IN p_name varchar(300),
    OUT newID int unsigned)
BEGIN
	select rtp_id
    from RTPlan
    where plan_label = p_label and plan_name = p_name
    limit 1
	into newID;
END //


DROP PROCEDURE IF EXISTS get_patient //
CREATE PROCEDURE get_patient (
    IN p_name varchar(200),
    OUT newID int unsigned)
BEGIN
	select patient_id
    from Patient
    where anonymization_detail = p_name
    limit 1
	into newID;
END //


DROP PROCEDURE IF EXISTS get_dvh //
CREATE PROCEDURE get_dvh (
    IN gs_id int unsigned,
    OUT newID int unsigned)
BEGIN
	select dvh_id
    from DVH
    where group_structure_id = gs_id
    limit 1
	into newID;
END //




/* Procedure to clean the db */
DROP PROCEDURE IF EXISTS clean_macaron_db //
CREATE PROCEDURE clean_macaron_db()
BEGIN
	DELETE FROM GroupPlanMetric WHERE group_plan_metric_id > 0;
	DELETE FROM DVHDetail WHERE dvh_detail_id > 0;
	DELETE FROM DVH WHERE dvh_id > 0;
	DELETE FROM StructureFeature WHERE structure_feature_id > 0;
	DELETE FROM GroupStructure WHERE group_structure_id > 0;
	DELETE FROM DicomGroup WHERE group_id > 0;
	DELETE FROM Structure WHERE structure_id > 0;
	DELETE FROM RTDose WHERE rtd_id > 0;
	DELETE FROM RTPlan WHERE rtp_id > 0;
	DELETE FROM Patient WHERE patient_id > 0;
END //

DELIMITER ;

call populate_db();

/*
--------------------------------------------------------------------------------------------------
								            VIEWS
--------------------------------------------------------------------------------------------------
*/

drop view if exists seeRadiomicFeatures;
CREATE VIEW seeRadiomicFeatures AS 
	SELECT group_name as "Patient Name", full_name as "Structure Name", structure_type as "Structure Type", feature_name as "Feature Name", 
		category_name as "Feature Category", feature_value as "Value" 
    from (StructureFeature join RadiomicFeature using (feature_id) 
		inner join FeatureCategory on RadiomicFeature.feature_category = FeatureCategory.category_id)
        join GroupStructure using(group_structure_id)
        join DicomGroup using(group_id)
        join Structure using(structure_id);


/* View to scan Plan Metrics */
drop view if exists seePlanMetrics;
CREATE VIEW seePlanMetrics AS 
	SELECT group_name as "Patient Name", metric_name as "Metric Name", plan_metric_value as "Value", metric_unit as "Measure Unit", 
		plan_metric_img as "Image File"
    from ((GroupPlanMetric join PlanMetric using(plan_metric_id))
        join DicomGroup using(group_id));

        
drop view if exists seeStructures;
CREATE VIEW seeStructures AS 
	select group_name as "Patient Name", full_name as "Structure Name", structure_type as "Structure Type", 
		concat('{', color_R, ', ', color_G, ', ', color_B, '}') as "Structure Color RGB" 
	from structure join groupstructure using(structure_id) 
		join dicomgroup using (group_id) 
			join patient using(patient_id)
	order by group_name, full_name;
    

drop view if exists seeDVH;
CREATE VIEW seeDVH AS 
	select group_name as "Patient Name", full_name as "Structure Name", structure_type as "Structure Type",
		image_path, abs_volume, diagram_type, volume_unit, dose_unit, max_dose, min_dose, mean_dose, D100, D98, D95, D2cc
	from structure join groupstructure using(structure_id) 
		join dicomgroup using (group_id) 
			join patient using(patient_id)
				join dvh using(group_structure_id)
	order by group_name, full_name;
    
    
drop view if exists seeControlPointMetrics;
CREATE VIEW seeControlPointMetrics AS 
	select group_name as "Patient Name", cp_index as "CP Index", metric_name as "Metric Name", cp_metric_value as "Metric Value"
	from groupcontrolpointmetric join dicomgroup using (group_id) 
			join patient using(patient_id)
				join controlpointmetric using(cp_metric_id)
	order by group_name, cp_index;


use macaron;

select * from rtplan;
select * from seeControlPointMetrics;

call add_control_point_metric_values(3, 1, 0.0, 54.4, 16.3125, 210.0, 40, 32, 4, 36, 660.0, 132.0, 2610.0, @id);

call add_control_point_metric_value(3, "minAperture", 10, 1, @newID);

SELECT cp_metric_id
    FROM ControlPointMetric
    WHERE metric_name = "minAperture";

select * from seeDVH;

select * from rtdose;

select * from dicomgroup;

select * from groupstructure;

select * from GroupControlPointMetric;
