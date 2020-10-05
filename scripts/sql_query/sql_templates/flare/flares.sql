
-- find patients with RA
create volatile table ra_cds as 
(
select *
from RWD_VDM_IMSPM.PP_DX_LOOKUP
where lower(Diagnosis_desc) like '%rheumatoid arthritis%'
	AND batch_title = 'IMSPM 2020Q2 VDM'
) with data on commit preserve rows;

select * 
from ra_cds;

select top 10 * 
from RWD_VDM_IMSPM.CLAIMS
where 
	diag1 in (select dx_cd from ra_cds);



select batch_title, valid_start, valid_end, count(*), count(distinct pat_id)
from RWD_VDM_IMSPM.ENROLLMENT
group by batch_title, valid_start, valid_end;


-- use q2 2020 
select batch_title, min(valid_start), max(valid_end) from RWD_VDM_IMSPM.ENROLLMENT
group by batch_title;


select min(from_dt), max(from_dt)
from RWD_VDM_IMSPM.CLAIMS
where batch_title = 'IMSPM 2019Q3 VDM'; 

SELECT TOP 10 * 
FROM RWD_VDM_IMSPM.CLAIMS_workaround 
WHERE pat_id IS NOT NULL 
	AND load_id = '8553'
;


-- count up possible eligible people
SELECT enroll_time, in_time_window, COUNT(*), COUNT(DISTINCT pat_id)
FROM
(
SELECT pat_id, 
	enr_frst, 
	enr_last,
	mon_totl, 
	CASE WHEN mon_totl >= 18 
		THEN 1 
		ELSE 0 
		END enroll_time, 
	CASE WHEN (enr_frst >= '2012-01-01' AND enr_frst <= '2018-09-30')
		THEN 1 
		ELSE 0 
		END in_time_window
FROM RWD_VDM_IMSPM.ENROLLMENT
WHERE batch_title = 'IMSPM 2019Q1 VDM'
) AS temp
GROUP BY enroll_time, in_time_window; 





/* going to start by building up dataset by finding people that 
 * may likely meet the definition this hopefully speed up query times; 
 * create temp table */

CREATE VOLATILE TABLE eligible_pat_id AS 
	(
	SELECT 
		pat_id, 
		clm_frst, 
		clm_last, 
		nbr_clm_lines,
		enr_frst, 
		enr_last, 
		mon_totl, 
		der_sex, 
		der_yob,
		pat_region, 
		pat_state, 
		pat_zip3, 
		grp_indv_cd, 
		mh_cd, 
		enr_rel		
	FROM
		(
		SELECT pat_id, 
			clm_frst, 
			clm_last, 
			nbr_clm_lines,
			enr_frst, 
			enr_last,
			mon_totl, 
			der_sex, 
			der_yob,
			pat_region, 
			pat_state, 
			pat_zip3, 
			grp_indv_cd, 
			mh_cd, 
			enr_rel,
			CASE WHEN mon_totl >= 18 
				THEN 1 
				ELSE 0 
				END enroll_time, 
			CASE WHEN (enr_frst >= '2012-01-01' AND enr_frst <= '2018-09-30')
				THEN 1 
				ELSE 0 
				END in_time_window
		FROM RWD_VDM_IMSPM.ENROLLMENT
		WHERE batch_title = 'IMSPM 2019Q1 VDM'
		) AS temp 
	WHERE enroll_time = 1 AND in_time_window = 1
	)
WITH DATA 
ON COMMIT PRESERVE ROWS
;


/* KEEP THIS ONE
 * IBD cd or uc claims 
 * 
 * Still need to remove diagnostic procedures observations
 * */

-- pivot one row per patient


SELECT 
	pat_id
	-- pivot wide chrons disease outpatient
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'outpatient')
		  THEN ibd_count 
		  ELSE NULL END) AS cd_outpat_count
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'outpatient')
		  THEN earliest_claim 
		  ELSE NULL END) AS cd_outpat_earliest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'outpatient')
		  THEN latest_claim 
		  ELSE NULL END) AS cd_outpat_latest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'outpatient')
		  THEN days_bw_claims
		  ELSE NULL END) AS cd_outpat_days_bw_claims
	-- pivot wide chrons disease inpatient
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'inpatient')
		  THEN ibd_count 
		  ELSE NULL END) AS cd_inpat_count
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'inpatient')
		  THEN earliest_claim 
		  ELSE NULL END) AS cd_inpat_earliest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'inpatient')
		  THEN latest_claim 
		  ELSE NULL END) AS cd_inpat_latest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'chrons_disease' AND inpat_outpat = 'inpatient')
		  THEN days_bw_claims
		  ELSE NULL END) AS cd_inpat_days_bw_claims
	-- pivot wide ulcerative colitis outpatient
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'outpatient')
		  THEN ibd_count 
		  ELSE NULL END) AS uc_outpat_count
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'outpatient')
		  THEN earliest_claim 
		  ELSE NULL END) AS uc_outpat_earliest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'outpatient')
		  THEN latest_claim 
		  ELSE NULL END) AS uc_outpat_latest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'outpatient')
		  THEN days_bw_claims
		  ELSE NULL END) AS uc_outpat_days_bw_claims
	-- pivot wide ulcerative colitis inpatient
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'inpatient')
		  THEN ibd_count 
		  ELSE NULL END) AS uc_inpat_count
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'inpatient')
		  THEN earliest_claim 
		  ELSE NULL END) AS uc_inpat_earliest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'inpatient')
		  THEN latest_claim 
		  ELSE NULL END) AS uc_inpat_latest_claim
	, MAX(CASE WHEN 
			(ibd_claim = 'ulcerative_colitis' AND inpat_outpat = 'inpatient')
		  THEN days_bw_claims
		  ELSE NULL END) AS uc_inpat_days_bw_claims,
	-- ibd type
	CASE WHEN 
		(ZEROIFNULL(cd_outpat_count) + ZEROIFNULL(cd_inpat_count)) > 
		(ZEROIFNULL(uc_outpat_count) + ZEROIFNULL(uc_inpat_count))
		THEN 'chrons_disease'
		ELSE 'ulcerative_colitis'
		END ibd_type
FROM 
	(
	-- count number of claims for a given ibd subtype
	SELECT 
		pat_id, 
		inpat_outpat, 
		ibd_claim, 
		COUNT(*) AS ibd_count, 
		MIN(from_dt) AS earliest_claim, 
		MAX(from_dt) AS latest_claim,
		latest_claim - earliest_claim AS days_bw_claims,
		CASE WHEN 
			-- at least 1 inpatient visit
			(inpat_outpat = 'inpatient' AND ibd_count >= 1)
				THEN 1 
			WHEN 
			-- at least 2 outpatient visits at least a day apart
			(inpat_outpat = 'outpatient' AND ibd_count >=2 AND days_bw_claims >=1)
				THEN 1 
			ELSE 0 
			END inclusion_flag
		, MAX(proc_cde) AS proc_code
      	-- start by casting proc to int
      	, TRYCAST(proc_code AS INT) AS proc_int 
      	-- flag diagnostic procedures
      	, CASE WHEN (
      	    (proc_int >= 70010 AND proc_int <= 76999)
      	      OR (proc_int >= 78000 AND proc_int <= 78799)
      			  OR (proc_int >= 80000 AND proc_int <= 89999))
	          THEN 1 
	        ELSE 0 
	       END diag_exclude_flag
	FROM 
		(
		SELECT TOP 100
			pat_id,
			pos, 
			CASE WHEN pos = '21'
					THEN 'inpatient'
				WHEN pos IN ('02', '11', '22', '24', '26') 
					THEN 'outpatient'
					ELSE NULL
				END inpat_outpat,
			from_dt, 
			to_dt,
			proc_cde, 
			-- find out which claim is most common at a given visit 
			-- cd will be 1 and uc will be -1, after summing up across columns + will be cd - will be uc 0 will be ic
			CASE WHEN diag1 LIKE ANY ('555%', 'K50%') 
				THEN 1 
				WHEN diag1 LIKE ANY ('556%', 'K51%')
				THEN -1 
				ELSE 0
				END ibd_type1, 
			CASE WHEN diag2 LIKE ANY ('555%', 'K50%') 
				THEN 1 
				WHEN diag2 LIKE ANY ('556%', 'K51%')
				THEN -1 
				ELSE 0
				END ibd_type2, 
			CASE WHEN diag3 LIKE ANY ('555%', 'K50%') 
				THEN 1 
				WHEN diag3 LIKE ANY ('556%', 'K51%')
				THEN -1 
				ELSE 0
				END ibd_type3, 
			CASE WHEN diag4 LIKE ANY ('555%', 'K50%') 
				THEN 1 
				WHEN diag4 LIKE ANY ('556%', 'K51%')
				THEN -1 
				ELSE 0
				END ibd_type4, 
			CASE WHEN diag5 LIKE ANY ('555%', 'K50%') 
				THEN 1 
				WHEN diag5 LIKE ANY ('556%', 'K51%')
				THEN -1 
				ELSE 0
				END ibd_type5, 
			CASE WHEN diag6 LIKE ANY ('555%', 'K50%') 
				THEN 1 
				WHEN diag6 LIKE ANY ('556%', 'K51%')
				THEN -1 
				ELSE 0
				END ibd_type6, 
			-- stopped here, could go through all 12 dx but this should be good enough
			CASE WHEN 
				(ibd_type1 + ibd_type2 + ibd_type3 + ibd_type4 + ibd_type5 + ibd_type6) > 0
				THEN 'chrons_disease' 
				WHEN 
				(ibd_type1 + ibd_type2 + ibd_type3 + ibd_type4 + ibd_type5 + ibd_type6) < 0
				THEN 'ulcerative_colitis'
				ELSE 'indeterminate colitis'
				END ibd_claim 
		FROM RWD_VDM_IMSPM.CLAIMS 
		WHERE batch_title = 'IMSPM 2019Q1 VDM' 
			-- limit to certain places of service 
			AND 
				pos IN ('02', '11', '21', '22', '24', '26') 
			-- limit to study date window
			AND 
				(from_dt >= '2012-01-01' AND from_dt <= '2018-09-30')
			AND 
				(
				diag1 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag2 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag3 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag4 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag5 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag6 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag7 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag8 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag9 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag10 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag11 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag12 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				)
		) AS temp
	GROUP BY pat_id, inpat_outpat, ibd_claim
	WHERE ibd_claim <> 'indeterminate colitis'
	    AND diag_exclude_flag <> 1
	) AS temp2
GROUP BY pat_id
WHERE inclusion_flag = 1
;



select top 10 * from phc_543.ibd_patients;
/* KEEP THIS ONE
 * TNF USE IF earliest TNF, that should be the index date
 * */


SELECT c.* 
	, d.product_name AS ndc_trt
FROM 
	(
	SELECT a.*
		, b.procedure_desc AS proc_trt	
	FROM 
		(
		SELECT pat_id 
			, pos 
			, proc_cde 
			, ndc 	
			, diag1
			, diag2
			, diag3
			, diag4
			, from_dt
		FROM RWD_VDM_IMSPM.CLAIMS 
		WHERE batch_title = 'IMSPM 2019Q1 VDM' 
				-- limit to study date window
				AND 
					(from_dt >= '2012-01-01' AND from_dt <= '2018-09-30')
				-- ndc and hcpcs
				AND (
					ndc IN ('00074254003', '54868482200')
					OR proc_cde IN ('J1745', 'J3380', 'C9026')
					)
		) AS a
	-- join hcpc infusion procedures
	LEFT JOIN RWD_VDM_IMSPM.PP_PR_LOOKUP AS b
	ON a.proc_cde = b.procedure_cd
	WHERE b.batch_title = 'IMSPM 2019Q1 VDM'
	) AS c
-- join ndc
LEFT JOIN RWD_VDM_IMSPM.PP_RX_LOOKUP AS d 
ON c.ndc = d.ndc 
WHERE d.batch_title = 'IMSPM 2019Q1 VDM'
;



select top 10 * 
FROM RWD_VDM_IMSPM.PP_PR_LOOKUP
WHERE batch_title = 'IMSPM 2019Q1 VDM';

select top 10 * from phc_543.ibd_patients;

-- test area


select ibd_type, 
count(*) from phc_543.ibd_patients
group by ibd_type;


select top 10 * from phc_543.ibd_patients;


SELECT TOP 10 * 
FROM RWD_VDM_IMSPM.CLAIMS
WHERE batch_title = 'IMSPM 2019Q1 VDM' 
AND (from_dt >= '2012-01-01' AND from_dt <= '2018-09-30');

SELECT COUNT(*)
FROM RWD_VDM_IMSPM.ENROLLMENT
WHERE batch_title = 'IMSPM 2019Q1 VDM' 
AND (enr_frst >= '2012-01-01' AND enr_last <= '2018-09-30');


SELECT TOP 10 * 
FROM RWD_VDM_IMSPM.CLAIMS
WHERE batch_title = 'IMSPM 2019Q1 VDM';


-- lookup
SELECT * FROM RWD_VDM_IMSPM.PP_POS_LOOKUP;
-- diagnosis
SELECT * FROM RWD_VDM_IMSPM.PP_DX_LOOKUP
WHERE diagnosis_desc LIKE UPPER('%rheumatoid arthritis%') 
ORDER BY dx_cd; 
-- drug
SELECT DISTINCT(NDC) FROM RWD_VDM_IMSPM.PP_RX_LOOKUP
WHERE LOWER(generic_name) LIKE ('%tofacitinib%'); 

SELECT TOP 10 * FROM RWD_VDM_IMSPM.PP_RX_LOOKUP;

SELECT * FROM RWD_VDM_IMSPM.PP_RX_LOOKUP
WHERE LOWER(product_name) = 'humira'; 

-- procedure
SELECT *
FROM RWD_VDM_IMSPM.PP_PR_LOOKUP
WHERE procedure_cd LIKE '700%'
ORDER BY procedure_cd
; 

SELECT DISTINCT(procedure_cd), procedure_desc, 
	TRYCAST(procedure_cd AS INT) AS proc_int, 
	CASE WHEN (
		(proc_int >= 70010 AND proc_int <= 76999)
		OR (proc_int >= 78000 AND proc_int <= 78799)
		OR (proc_int >= 80000 AND proc_int <= 89999))
	THEN 1 
	ELSE 0 
	END diag_exclude_flag
FROM RWD_VDM_IMSPM.PP_PR_LOOKUP
WHERE (proc_int >= 70010 AND proc_int <= 76999)
	OR (proc_int >= 78000 AND proc_int <= 78799)
	OR (proc_int >= 80000 AND proc_int <= 89999)
ORDER BY procedure_cd
; 

SELECT TOP 10 * 
FROM RWD_VDM_IMSPM.CLAIMS
WHERE batch_title = 'IMSPM 2019Q1 VDM'



SELECT procedure_cd, CAST(procedure_cd AS int)
FROM RWD_VDM_IMSPM.PP_PR_LOOKUP
WHERE procedure_cd LIKE '7699%'
ORDER BY procedure_cd
; 



-- count of index date
SELECT COUNT(*), COUNT(DISTINCT pat_id)
FROM phc_543.treatment
WHERE trt_class = 'tnf' AND trt_sequence = 1
	AND n_trt >= 2 AND trt_days > 0
;


CREATE VOLATILE TABLE tnf_index AS 
	(
	SELECT pat_id
		, first_trt_date AS index_date
		, trt 
		, trt_class
	FROM phc_543.treatment
	WHERE trt_class = 'tnf' AND trt_sequence = 1
		AND n_trt >= 2 AND trt_days > 0
	) 
WITH DATA 
ON COMMIT PRESERVE ROWS;


select count(*), count(distinct pat_id) from tnf_index;


CREATE VOLATILE TABLE tnf_ibd AS 
	(
	SELECT 
		a.*
		, b.ibd_count 
		, b.ibd_earliest_claim
		, b.ibd_latest_claim
		, ibd_type
	FROM tnf_index AS a
	INNER JOIN phc_543.ibd_patients AS b
	ON 
		(a.pat_id = b.pat_id) 
		AND 
		(a.index_date - 180 <= b.ibd_earliest_claim 
		AND a.index_date >= b.ibd_earliest_claim)
	)
WITH DATA 
ON COMMIT PRESERVE ROWS;


select top 50 * from tnf_ibd;

select count(*), count(distinct pat_id) from tnf_ibd;

SELECT trt_sequence, count(*) from phc_543.treatment
group by trt_sequence;




  		  
-- stopped here; find window of overlap
CREATE VOLATILE TABLE second_treatment AS
	(
	SELECT
	a.*
	, b.ibd_count
	, b.ibd_earliest_claim 
	, b.ibd_latest_claim
	, b.ibd_type
	FROM 
		(
		SELECT 
			a.pat_id
			-- first treatment
			, MIN(CASE WHEN (a.trt_sequence = 1)
				THEN a.trt_class ELSE NULL END) AS trt1_class
			, MIN(CASE WHEN (a.trt_sequence = 1)
				THEN a.trt ELSE NULL END) AS trt1
			, MIN(CASE WHEN (a.trt_sequence = 1)
				THEN a.first_trt_date ELSE NULL END) AS trt1_index_date  
			, MAX(CASE WHEN (a.trt_sequence = 1)
				THEN a.last_trt_date ELSE NULL END) AS trt1_last_date	
			-- second treatment
			, MIN(CASE WHEN (a.trt_sequence = 2)
				THEN a.trt_class ELSE NULL END) AS trt2_class
			, MIN(CASE WHEN (a.trt_sequence = 2)
				THEN a.trt ELSE NULL END) AS trt2
			, MIN(CASE WHEN (a.trt_sequence = 2)
				THEN a.first_trt_date ELSE NULL END) AS trt2_switch_date  
			, MAX(CASE WHEN (a.trt_sequence = 2)
				THEN a.last_trt_date ELSE NULL END) AS trt2_last_date	
			-- find Patients with at least one pharmacy claim during 12-month post-index for a different TNF or MOA; switch date = date of earliest switch
			, CASE WHEN (trt2_switch_date - trt1_index_date) <= 365
				THEN 'yes' ELSE 'no' END second_treatment_criteria
		FROM phc_543.treatment AS a
		GROUP BY a.pat_id
		HAVING second_treatment_criteria = 'yes'
		) AS a 
	INNER JOIN tnf_ibd AS b 
	ON a.pat_id = b.pat_id
	)
WITH DATA 
ON COMMIT PRESERVE ROWS;

select count(*) from second_treatment;

drop table over_18;

-- 18 yo on switch date
CREATE VOLATILE TABLE over_18 AS 
	(
	SELECT 
		a.*
		, (YEAR(a.trt2_switch_date) - yob) AS age_at_switch 
		, b.der_sex AS sex 
		, b.der_yob AS yob 
		, b.pat_region
		, b.pat_state
		, b.pat_zip3
		, b.grp_indv_cd
		, b.mh_cd 
		, b.enr_rel
		, b.estring
		, b.clm_frst 
		, b.clm_last
		, b.nbr_clm_lines
		, b.enr_frst
		, b.enr_last 
		, b.mon_totl
		, b.mxce_fst
		, b.mxce_lst
	FROM second_treatment AS a
	LEFT JOIN 
		(
		SELECT *
		FROM RWD_VDM_IMSPM.ENROLLMENT 
		WHERE batch_title = 'IMSPM 2019Q1 VDM'
		)AS b
	ON a.pat_id = b.pat_id
	WHERE age_at_switch >= 18
	)
WITH DATA
ON COMMIT PRESERVE ROWS;


select top 10 * from over_18;

-- find comorbidites that may have occured during 6 month pre-index period through switch


CREATE VOLATILE TABLE no_autoimmune_comorb AS
  (
SELECT e.*
FROM
(
SELECT 
	pat_id
	, MIN(from_dt) AS first_comorb_dt
	, MAX(from_dt) AS last_comorb_dt
	, CASE WHEN pat_id IS NOT NULL
		THEN 'yes'
		ELSE NULL
		END autoimmune_flag
FROM 
(
SELECT 
	a.pat_id 
	, a.from_dt 
FROM RWD_VDM_IMSPM.CLAIMS AS a
INNER JOIN over_18 AS b 
ON (a.pat_id = b.pat_id
	AND 
	(a.from_dt >= b.trt1_index_date - 180 AND a.from_dt <= b.trt2_switch_date)
	)
WHERE batch_title = 'IMSPM 2019Q1 VDM' 
	AND 
		pos IN ('02', '11', '21', '22', '24', '26') 
     	-- limit to study date window
    AND 
    	(from_dt >= '2012-01-01' AND from_dt <= '2018-09-30')
    AND 
    (
      				diag1 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag2 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag3 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag4 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag5 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag6 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag7 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag8 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag9 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag10 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag11 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				OR diag12 LIKE ANY ('7140', '7141', '7142', 'M05%', 'M06%')
      				)
) AS c
GROUP BY pat_id
-- join with ibd cohort over 18 on switch
) AS d
RIGHT JOIN over_18 AS e 
ON d.pat_id = e.pat_id
WHERE autoimmune_flag IS NULL
) 
WITH DATA ON COMMIT PRESERVE ROWS
;


-- continous enrollment in med and pharm benefits
select top 20 * from RWD_VDM_IMSPM.ENROLLMENT2
                       		WHERE string_type = 'ben_rx'
                       			AND '2020-03-17' BETWEEN CAST(valid_start AS DATE) AND CAST(valid_end AS DATE);


                      CREATE VOLATILE MULTISET TABLE enrollment2_med AS (
                       SELECT DISTINCT a.pat_id
                       	, OREPLACE(b.string_value, 'Y', '*Y') AS string_value
                       -- table with patient ids you want to find continous enrollment on
                       FROM no_autoimmune_comorb AS a 
                       INNER JOIN 
                       		(
                       		SELECT pat_id, 
                       			OREPLACE(SUBSTR(string_value,1,219),'-','*-') AS string_value 
                       		FROM RWD_VDM_IMSPM.ENROLLMENT2 
                       		WHERE string_type = 'ben_rx'
                       			AND '2020-03-17' BETWEEN CAST(valid_start AS DATE) AND CAST(valid_end AS DATE)
                       		) AS b 
                       	ON a.pat_id = b.pat_id
                       ) 
                       WITH DATA 
                      ON COMMIT PRESERVE ROWS; 

select top 50 * from enrollment2_med;

HELP VOLATILE TABLE;
drop table enroll_med_cols;
    CREATE VOLATILE MULTISET TABLE enroll_med_cols AS (
    SELECT *
    FROM  TABLE (STRTOK_SPLIT_TO_TABLE(enrollment2_med.pat_id,enrollment2_med.string_value,'*')
    RETURNS ( outkey VARCHAR(16), tokennum INTEGER, token VARCHAR(1))) as dt
    ) with data on commit preserve rows;
    
   
select top 50 * from enroll_med_cols;


CREATE VOLATILE MULTISET TABLE enroll_med_cols_clean AS (
      SELECT distinct outkey as pat_id
      , tokennum
      , token 
      FROM  enroll_med_cols
      WHERE token <> '-' 
    ) with data on commit preserve rows;
    
select top 50 * from enroll_med_cols_clean;


CREATE VOLATILE MULTISET TABLE enroll_med_dts AS (
    SELECT distinct pat_id
    , ADD_MONTHS('2001-01-01',tokennum -1) as dtstart
    , ADD_MONTHS('2001-01-01',tokennum)-1 as dtend
    FROM  enroll_med_cols_clean 
  ) with data on commit preserve rows;
  
 
 select top 50 * from enroll_med_dts;
 

CREATE VOLATILE MULTISET TABLE med_periods AS (
    SELECT DISTINCT starts.pat_id, starts.dtstart AS period_start, ends.dtend AS period_stop
    FROM ( 
          SELECT pat_id, dtstart, ROW_NUMBER() OVER (ORDER BY pat_id, dtstart) AS rn
          FROM ( 
            SELECT pat_id, dtstart, dtend, 
            CASE WHEN dtstart LE prev_end + (0 + 1) THEN 'cont' ELSE 'new' END AS start_status,
            CASE WHEN dtend GE next_start - (0 + 1) THEN 'cont' ELSE 'new' END AS end_status
            FROM ( 
              SELECT pat_id, dtstart, dtend, 
              COALESCE(MAX(dtend) OVER (PARTITION BY pat_id ORDER BY dtstart,dtend ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING), null) as prev_end,
              COALESCE(MIN(dtstart) OVER (PARTITION BY pat_id ORDER BY dtstart,dtend ROWS BETWEEN 1 FOLLOWING AND 1 FOLLOWING), null) as next_start
              FROM enroll_med_dts 
            )  AS t1
         WHERE start_status= 'new'
        )  AS t2
      ) AS starts (pat_id, dtstart, rn),
    ( 
      SELECT pat_id, dtend, ROW_NUMBER() OVER (ORDER BY pat_id, dtstart) AS rn
      FROM ( 
        SELECT pat_id, dtstart, dtend,
        CASE WHEN dtstart LE prev_end + (0 + 1) THEN 'cont' ELSE 'new' END AS start_status,
        CASE WHEN dtend GE next_start-(0 + 1) THEN 'cont' ELSE 'new' END AS end_status
        FROM ( 
          SELECT pat_id, dtstart, dtend,
          COALESCE(MAX(dtend) OVER (PARTITION BY pat_id ORDER BY dtstart,dtend ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING), null) as prev_end,
          COALESCE(MIN(dtstart) OVER (PARTITION BY pat_id ORDER BY dtstart,dtend ROWS BETWEEN 1 FOLLOWING AND 1 FOLLOWING), null) as next_start
          FROM enroll_med_dts 
        ) AS t3
        WHERE end_status= 'new'
        ) AS t4
    ) AS ends (pat_id, dtend, rn)
    WHERE starts.rn = ends.rn 
  ) WITH DATA ON COMMIT PRESERVE ROWS;
  
 
select top 50 * from med_periods;

select count(*)
from 
(
select 
	a.*
	, b.period_start 
	, b.period_stop
from no_autoimmune_comorb AS a
inner join med_periods AS b 
on a.pat_id = b.pat_id
	and (a.trt1_index_date - 180 >= b.period_start AND b.period_stop >= a.trt2_switch_date + 365 )
) as temp;


select batch_title, count(*) from RWD_VDM_IMSPM.ENROLLMENT
group by batch_title;

select count(pat_id) from phc_543.treatment;

select top 10 * from phc_543.cohort;


select top 10 * from phc_543.ibd_patients;


SELECT pos, count(*)
FROM RWD_VDM_IMSPM.CLAIMS_WORKAROUND 
GROUP BY pos
WHERE pat_id IS NOT NULL /* load_id 8533 is Q4 workaround created by MDH to speed up query */
AND load_id = '8553';



SELECT 
	pat_id,
	ibd_claim,
	COUNT(*) AS ibd_count
FROM
  (
  SELECT top 50 
    pat_id
    , CASE WHEN diag1 LIKE ANY ('555%', 'K50%') 
    		THEN 1 
      	WHEN diag1 LIKE ANY ('556%', 'K51%')
      		THEN -1 
      	ELSE 0
      	END ibd_type1 
      			, CASE WHEN diag2 LIKE ANY ('555%', 'K50%') 
      				    THEN 1 
      				  WHEN diag2 LIKE ANY ('556%', 'K51%')
      				    THEN -1 
      				  ELSE 0
      				  END ibd_type2
      			, CASE WHEN diag3 LIKE ANY ('555%', 'K50%') 
      		  		  THEN 1 
      	  			WHEN diag3 LIKE ANY ('556%', 'K51%')
      		  		  THEN -1 
      				  ELSE 0
      				  END ibd_type3 
      			, CASE WHEN diag4 LIKE ANY ('555%', 'K50%') 
      			  	  THEN 1 
      		  		WHEN diag4 LIKE ANY ('556%', 'K51%')
      			  	  THEN -1 
      				  ELSE 0
      				  END ibd_type4 
      			, CASE WHEN diag5 LIKE ANY ('555%', 'K50%') 
      				    THEN 1 
      				  WHEN diag5 LIKE ANY ('556%', 'K51%')
      				    THEN -1 
      				  ELSE 0
      				  END ibd_type5 
      			, CASE WHEN diag6 LIKE ANY ('555%', 'K50%') 
      				    THEN 1 
      			  	WHEN diag6 LIKE ANY ('556%', 'K51%')
      				    THEN -1 
      				  ELSE 0
      				  END ibd_type6 
      			-- stopped here, could go through all 12 dx but this should be good enough
      			, CASE WHEN 
      				(ibd_type1 + ibd_type2 + ibd_type3 + ibd_type4 + ibd_type5 + ibd_type6) > 0
      				    THEN 'chrons_disease' 
      				  WHEN 
      				(ibd_type1 + ibd_type2 + ibd_type3 + ibd_type4 + ibd_type5 + ibd_type6) < 0
      				  THEN 'ulcerative_colitis'
      				  ELSE 'indeterminate colitis'
      				  END ibd_claim
  FROM RWD_VDM_IMSPM.CLAIMS_WORKAROUND 
  WHERE pat_id IS NOT NULL 
    -- load_id 8533 is Q4 workaround created by MDH to speed up query 
    AND load_id = '8553'
      -- Subset conf_num is not null to subset to inpatient claims
    AND 
      conf_num IS NOT NULL
			AND 
				(from_dt >= '2012-01-01' AND from_dt <= '2018-09-30')
			AND 
				(
				diag1 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag2 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag3 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag4 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag5 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag6 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag7 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag8 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag9 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag10 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag11 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				OR diag12 LIKE ANY ('555%', 'K50%', '556%', 'K51%')
				)  
	) AS temp 
GROUP BY pat_id, ibd_claim;


SELECT *
FROM RWD_VDM_IMSPM.PP_DX_LOOKUP 
WHERE dx_cd LIKE ('555%', 'K50%', '556%', 'K51%') 
 AND batch_title = 'IMSPM 2019Q1 VDM'; 
 


SELECT 
	ndc
	, product_name
	, generic_name
FROM RWD_VDM_IMSPM.PP_RX_LOOKUP
WHERE LOWER(generic_name) LIKE '%vedolizumab%'
	; 
	


SELECT 
	procedure_cd 
	, procedure_desc
FROM RWD_VDM_IMSPM.PP_PR_LOOKUP
WHERE LOWER(procedure_desc) LIKE '%vedolizumab%'
	AND LOWER(procedure_cd) NOT LIKE 's%'
	AND batch_title = 'IMSPM 2019Q4 VDM'
ORDER BY procedure_cd; 


-- market scan
select top 10 * from RWD_VDM_CCAE.V02_CCAE_I
where admdate > '2010-01-01' 
	and age > 18 
	and valid_end >= '2020-08-20 20:00:00';


SELECT top 10 admdate, COUNT(*) AS n_hosp
FROM 
    (
     SELECT *
     FROM RWD_VDM_CCAE.V02_CCAE_I
     WHERE admdate >= '2020-01-01'
     	AND (DX1 like any ('486%', 'J%') or DX2 like any ('486%', 'J%'))
        AND AGE > 18
        AND valid_end >= '2020-08-20 20:00:00'
    ) AS temp
GROUP BY admdate
order by admdate desc;

select count(*), count(distinct enrolid)
FROM RWD_VDM_CCAE.V02_CCAE_T 
where dtstart >= '2020-01-01';

SELECT top 10  d, COUNT(DISTINCT enrolid) AS n_enrolled
FROM RWD_VDM_CCAE.V02_CCAE_T
GROUP BY (dtstart - EXTRACT(DAY FROM dstart) + 1) AS d ;


SELECT year_month, COUNT(DISTINCT enrolid) AS n_enroll
FROM
(
SELECT 
	enrolid
	, dtend
	, dtstart
	, DTEND - EXTRACT(DAY FROM DTEND) + 1 AS year_month
FROM RWD_VDM_CCAE.V02_CCAE_T
WHERE valid_end >= '2020-08-20 20:00:00'
	AND dtstart >= '2016-01-01'
) AS temp
GROUP BY year_month;

