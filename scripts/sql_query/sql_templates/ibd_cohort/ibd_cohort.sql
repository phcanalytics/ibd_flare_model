CREATE TABLE ibd_flare.ibd_cohort AS
    (
    SELECT ptid, birth_yr, gender, race, ethnicity, region, division, 
        avg_hh_income, pct_college_educ, deceased_indicator, 
        date_of_death, provid_pcp, first_month_active, last_month_active, 
        uc_count, cd_count, outpatient_flag, inpat_er_obs_flag, 
        inpatient_flag, er_flag, ibd_visit_n, first_ibd_date, 
        EXTRACT(YEAR FROM first_ibd_date) AS index_year, 
        last_ibd_date, 
        -- set birth year of first month active as the first ibd date of visit
        CASE WHEN (birth_yr LIKE '%1929%')
                THEN index_year - '1929'
            WHEN (birth_yr LIKE '%Unknown%')
                THEN 9999
            ELSE index_year - birth_yr END age_at_index
    -- relaxed cohort criteria to drop criteria for incident IBD visit
    FROM ibd_cont_enroll
    WHERE age_at_index >= 18 AND age_at_index <> 9999
    )
WITH DATA;