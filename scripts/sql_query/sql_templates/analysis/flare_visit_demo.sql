/* Joining demographics to the flare_visits table. 
This temp table will be used to join baseline and 6 month
lab and immuno medications to. */
CREATE VOLATILE TABLE flare_visit_demo AS
    (
    SELECT *
    FROM
        (
        SELECT
            b.ptid, b.gender, b.race,
            b.ethnicity, b.birth_yr, b.deceased_indicator, 
            -- cast YYYYMM date of death as date
            TRUNC(
                CAST(b.date_of_death AS DATE FORMAT 'YYYYMM'),
                'RM') AS date_of_death, 
            b.uc_count, b.cd_count,
            b.first_ibd_date, b.last_ibd_date,
            b.age_at_index,
            a.visit_date, a.flare_date, 
            a.flare_6mo, a.prev_flare_sum,
            CASE WHEN (birth_yr LIKE '%1929%')
                THEN YEAR(visit_date) - '1929' 
                WHEN (birth_yr LIKE '%Unknown%')
                THEN NULL 
                ELSE YEAR(visit_date) - birth_yr END age
        FROM ibd_flare.flare_visits AS a
        LEFT JOIN ibd_flare.ibd_cohort AS b
        ON a.ptid = b.ptid
        ) AS temp
    -- exclude visits where date of death is missing or before visit_date
    WHERE date_of_death IS NULL
        OR date_of_death < visit_date 
    )
WITH DATA
ON COMMIT PRESERVE ROWS;