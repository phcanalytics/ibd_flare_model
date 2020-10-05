/* Create permanent table in IBD flare datalab */
CREATE TABLE ibd_flare.fecal_cal AS
    (
    SELECT b.*
    FROM ibd_flare.ibd_cohort AS a 
    INNER JOIN 
        (
        SELECT ptid, encid, test_name, test_type, 
            order_date, collected_date, test_result,
            relative_indicator, result_unit, normal_range,
            evaluated_for_range, value_within_range
        FROM RWD_VDM_OPTUM_EHRIBD.IBD_LABS 
        WHERE test_name LIKE '%Calprotectin%' 
         AND batch_title = 'OPTUM EHR IBD 2019 Oct Update 2'
        ) AS b
    ON a.ptid = b.ptid
    )
WITH DATA;