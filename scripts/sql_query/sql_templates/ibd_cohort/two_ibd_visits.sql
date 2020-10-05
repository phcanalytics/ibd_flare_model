CREATE VOLATILE TABLE two_ibd_visits AS
    (
    SELECT b.ptid, b.birth_yr, b.gender, b.race, b.ethnicity, b.region, 
        b.division, b.avg_hh_income, b.pct_college_educ,
        b.deceased_indicator, b.date_of_death, b.provid_pcp, 
        CAST(b.first_month_active AS DATE FORMAT 'YYYYMM') AS first_month_active, 
        CAST(b.last_month_active AS DATE FORMAT 'YYYYMM') AS last_month_active, 
        a.uc_count, a.cd_count, a.ibd_flag, a.outpatient_flag, a.inpat_er_obs_flag,
        a.inpatient_flag, a.er_flag, a.ibd_visit_n, a.first_date AS first_ibd_date, 
        a.last_date AS last_ibd_date
    FROM 
        (
        SELECT ptid, uc_count, cd_count, outpatient_flag, inpat_er_obs_flag,
        	inpatient_flag, er_flag, ibd_visit_n, first_date, last_date,
            -- Flag persons with IBD visits and with at least one outpatient visit
            CASE WHEN (uc_count > 0 AND cd_count > 0)
                    THEN 'indeterminate colitis'
                WHEN (uc_count > 0 AND cd_count = 0)
                    THEN 'ulcerative colitis'
                WHEN (uc_count = 0 AND cd_count > 0)
                    THEN 'chrons disease'
                    ELSE 'other' END ibd_flag
        FROM
            (
            SELECT ptid, SUM(uc_count) AS uc_count, SUM(cd_count) AS cd_count, 
             MAX(outpatient_flag) AS outpatient_flag,
             MAX(inpat_er_obs_flag) AS inpat_er_obs_flag,
             MAX(inpatient_flag) AS inpatient_flag,
             MAX(er_flag) AS er_flag,
             MAX(ibd_visit_n) AS ibd_visit_n, 
             MIN(interaction_date) AS first_date,
             MAX(interaction_date) AS last_date
            FROM ibd_visit
            GROUP BY ptid
            ) AS temp
        -- Logic for 2 visits with at least one outpatient
        WHERE (outpatient_flag = 1 AND ibd_visit_n >= 2) AND 
        	-- Logic for visits that aren't on the same date
        	(first_date <> last_date) AND 
        	-- Logic for time period of study
            (first_date >= '2007-01-01' AND last_date <= '2017-12-31')
        ) AS a
        INNER JOIN RWD_VDM_OPTUM_EHRIBD.IBD_PATIENT AS b 	
        ON a.ptid = b.ptid
        WHERE batch_title = 'OPTUM EHR IBD 2019 Apr'  
    ) 
WITH DATA
ON COMMIT PRESERVE ROWS;