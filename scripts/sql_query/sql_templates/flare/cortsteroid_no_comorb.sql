/* Create table that identifies corticosteroids with no comorbidity */
CREATE VOLATILE TABLE cortsteroid_no_comorb AS
    (
    SELECT ptid, rxdate, day_supply_criteria, flare_cat
    FROM 
    	(
	    SELECT ptid, rxdate, day_supply_criteria, flare_cat, 
	    	CAST(rxdate AS DATE FORMAT 'YYYY-MM-DD') AS format_date,
			-- lag function to find last date
			LAG(format_date) OVER (PARTITION BY ptid ORDER BY rxdate) AS lag_date,
			-- calculate difference since last date; first inpatient observations are NULL
			CASE WHEN lag_date IS NOT NULL
				THEN rxdate - CAST(lag_date AS DATE FORMAT 'YYYY-MM-DD')
				ELSE NULL END date_diff 
	    FROM
	    	(
			SELECT b.ptid, b.rxdate, b.day_supply_criteria, b.flare_cat
			FROM
				( 
				-- Find comorbidity encounters in close proximity to the outpatient steroid
				SELECT ptid, encid, diag_date, diagnosis_cd, diagnosis_cd_type,
				CASE WHEN (
					-- COPD
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '491%') OR
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '492%') OR
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '496%') OR
					-- Check ICD10 definition with Diana
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'J44%') OR
					-- Asthma
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '493%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'J45%') OR
					-- RA
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '714%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'M05%') OR		
					-- lupus
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '710%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'L93%') OR		
					-- Dermatitis
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '69%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'L%') OR	
					-- Bronchitis
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '490%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'J20%') OR	
					-- Sinusitis
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '461%') OR
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '473%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'J01%') OR	
					-- Rhinitis
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '472%') OR
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '477%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'J30%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'J31%') OR
					-- Polymyalgia rheumatica
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '725%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'M353') OR		
					-- Cluster headaches
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '339%') OR
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'G440%') OR
					-- autoimmune hepatitis
					(diagnosis_cd_type = 'ICD9' AND diagnosis_cd LIKE '57142') OR	
					(diagnosis_cd_type = 'ICD10' AND diagnosis_cd LIKE 'K754')
		            )
					THEN 1 ELSE 0 END comorbid_flag
			FROM RWD_VDM_OPTUM_EHRIBD.IBD_DIAGNOSIS
			WHERE comorbid_flag = 1 AND encid IS NOT NULL 
		            AND batch_title = 'OPTUM EHR IBD 2019 Apr' 
				) AS a
		     -- keep only outpatient steroids without a comorbidity flag
			RIGHT JOIN outpatient_oral_cortsteroid AS b
			ON (a.ptid = b.ptid) AND
				(b.rxdate >= a.diag_date - 7 AND b.rxdate <= a.diag_date) 
			WHERE comorbid_flag IS NULL
		    ) AS temp
	) AS temp2
	-- exclude steroid sequences within 90 days of each other
    WHERE (date_diff >= 90 OR date_diff IS NULL)
    )
WITH DATA
ON COMMIT PRESERVE ROWS;