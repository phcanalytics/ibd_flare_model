/* SQL query that joins ibd cohort demographics, 
immunosuppressive use, visits with flares, and 
lab values for analysis */ 
CREATE VOLATILE TABLE flare_predictors AS
    (
    SELECT e.id, e.vis_date, e.visit_n, e.flare_date, 
   		e.inpat_flare, e.interaction_type, e.steroid_flare,
        e.day_supply_criteria, e.flare_cat, e.flare_v1,
        e.prev_flare_v1_sum, e.flare_v2, e.prev_flare_v2_sum,
        e.first_immuno_med_date, e.immuno_med, e.gender, e.race, 
        e.birth_yr, e.deceased_indicator, e.date_of_death, e.first_ibd_date, 
        e.last_ibd_date, e.age_at_index, e.age, e.uc_count, 
        e.cd_count, e.disease_category, f.*
    FROM
        (
        SELECT c.ptid AS id, c.visit_date AS vis_date,
            c.visit_n, c.flare_date, c.inpat_flare, c.interaction_type, 
            c.steroid_flare, c.day_supply_criteria, c.flare_cat, c.flare_v1,
            c.prev_flare_v1_sum, c.flare_v2, c.prev_flare_v2_sum, 
            c.first_immuno_med_date, c.immuno_med, d.gender AS gender, 
            d.race AS race, d.birth_yr AS birth_yr, 
            d.deceased_indicator AS deceased_indicator, 
            -- cast YYYYMM date of death as date
            TRUNC(
                CAST(d.date_of_death AS DATE FORMAT 'YYYYMM'),
                'RM') AS date_of_death, 
            d.uc_count, d.cd_count,
            d.first_ibd_date, d.last_ibd_date,
            d.age_at_index,
            CASE WHEN (d.birth_yr LIKE '%1929%')
                THEN YEAR (vis_date) - '1929' 
                WHEN (d.birth_yr LIKE '%Unknown%')
                THEN NULL 
                ELSE YEAR (vis_date) - d.birth_yr END age,
            CASE WHEN uc_count > 0 AND cd_count = 0 
            	THEN 'ulcerative colitis' 
            	WHEN cd_count > 0 AND uc_count = 0 
            	THEN 'crohns disease' 
            	ELSE 'indeterminate colitis' END disease_category
        FROM 
            (
            SELECT a.ptid, a.visit_date, a.visit_n, a.flare_date, 
                a.inpat_flare, a.interaction_type, a.steroid_flare,
                a.day_supply_criteria, a.flare_cat, a.flare_v1,
                a.prev_flare_v1_sum, a.flare_v2, a.prev_flare_v2_sum,
                b.first_immuno_med_date,
                CASE WHEN visit_date >= first_immuno_med_date 
                    THEN 1 ELSE 0 END immuno_med
            FROM ibd_flare.flare_visits AS a
            LEFT JOIN immuno_med_date_window AS b 
            ON a.ptid = b.ptid
            ) AS c
        LEFT JOIN ibd_flare.ibd_cohort AS d
        ON c.ptid = d.ptid
        ) AS e
    LEFT JOIN ibd_flare.labs_wide AS f
    ON (e.id = f.ptid AND e.vis_date = f.visit_date)
    -- exclude visits where date of death is missing or before visit_date
    WHERE (date_of_death IS NULL OR date_of_death < vis_date) 
        AND gender <> 'Unknown'
    )
 WITH DATA 
 ON COMMIT PRESERVE ROWS;   