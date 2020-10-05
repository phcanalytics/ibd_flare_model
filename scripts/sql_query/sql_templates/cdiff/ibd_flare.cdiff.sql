/* Find C-diff observations for all patients in IBD cohort */
CREATE TABLE ibd_flare.cdiff AS
	(
	SELECT b.ptid, 
		a.diag_date, 
		a.diagnosis_cd, 
		a.diagnosis_cd_type,
		CASE WHEN a.diag_date IS NOT NULL
			THEN 'cdiff_dx'
			END cdiff_flag 
	FROM 
		(
		SELECT ptid, 
			diag_date, 
			MAX(diagnosis_cd) AS diagnosis_cd, 
			MAX(diagnosis_cd_type) AS diagnosis_cd_type 
		FROM RWD_VDM_OPTUM_EHRIBD.IBD_DIAGNOSIS 
		WHERE (encid IS NOT NULL 
			AND diagnosis_status = 'Diagnosis of' 
			AND (diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '00845%' OR 
				 diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'A04%') 
			AND batch_title = 'OPTUM EHR IBD 2019 Apr')
		GROUP BY ptid, diag_date
		) AS a
	INNER JOIN ibd_flare.ibd_cohort AS b
	ON a.ptid = b.ptid
	) 
WITH DATA ;