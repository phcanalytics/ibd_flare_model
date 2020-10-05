/* Script to identify those with at least two ibd visits and continous enrollment */
CREATE VOLATILE TABLE ibd_cont_enroll AS
    (
    SELECT ptid, birth_yr, gender, race, ethnicity, region, division, 
    	avg_hh_income, pct_college_educ, deceased_indicator, 
        date_of_death, provid_pcp, first_month_active, last_month_active, 
        uc_count, cd_count, ibd_flag, outpatient_flag, inpat_er_obs_flag, 
        inpatient_flag, er_flag, ibd_visit_n, first_ibd_date, last_ibd_date, 
        (first_ibd_date - first_month_active) AS days_prior_index, 
        (last_month_active - first_ibd_date) AS days_posterior_index
    FROM two_ibd_visits
    WHERE days_posterior_index >= 365
    )
WITH DATA
ON COMMIT PRESERVE ROWS;