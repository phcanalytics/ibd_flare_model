/* This script counts up the number of IBD-specific diagnoses */
CREATE VOLATILE TABLE ibd_enc_count AS
	(
	SELECT a.ptid, a.encid, a.uc_count, a.cd_count 
	FROM 
		(
		SELECT ptid, encid, SUM(uc_flag) AS uc_count, SUM(cd_flag) AS cd_count
			FROM
			-- nested table flagging icd9 and 10 codes that meet uc and cd criteria
			(
			SELECT ptid, encid, diag_date, diagnosis_cd_type, 
	            diagnosis_cd, diagnosis_status, description,
				-- Make new flag variable for uc
				CASE WHEN (diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '556%') 
                    OR (diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'K51%')
					THEN 1 ELSE 0 END uc_flag,
				-- Make new flag variable for cd
				CASE WHEN (diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '555%') 
                    OR (diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'K50%')
					THEN 1 ELSE 0 END cd_flag
			-- temp table disease_flag
			FROM RWD_VDM_OPTUM_EHRIBD.IBD_DIAGNOSIS
	        -- adding valid_start criteria to be able to reproduce
	        WHERE batch_title = 'OPTUM EHR IBD 2019 Apr' 
	            -- add criteria that it needs to be a diagnosis of
	            AND diagnosis_status = 'Diagnosis of'
	            -- and not missing encid so I can join
	            AND encid IS NOT NULL
	        ) AS disease_flag
		-- limit to observations with uc_flag 1 or cd_flag 1
		WHERE uc_flag = 1 OR cd_flag = 1
		-- count by patient id
		GROUP BY ptid, encid
	) AS a 
    -- join to existing cohort to limit query time
	INNER JOIN
		(
		SELECT ptid 
		FROM ibd_flare.ibd_cohort
		) AS b
	ON a.ptid = b.ptid
	) 
WITH DATA
ON COMMIT PRESERVE ROWS;
