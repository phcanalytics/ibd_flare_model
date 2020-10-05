/* This sql template creates a volatile table that calculates rolling mean of lab value,
max lab value, mean acceleration (change since last lab divided by time since last lab),
and max acceleration (change since last lab divided by time since last lab) using sequential 
lab values for each lab of interest for each person */
CREATE VOLATILE TABLE longitudinal_labs AS
    (
    SELECT ptid, encid, test_name, result_date, test_result, 
        rolling_mean, rolling_max, acc_value,
        -- rolling mean of accelerated value
        AVG(acc_value) OVER (PARTITION BY ptid, test_name 
                             ORDER BY result_date ROWS 1000 PRECEDING) AS rolling_mean_acc,
        -- rolling max of accelerated value
        MAX(acc_value) OVER (PARTITION BY ptid, test_name 
                             ORDER BY result_date ROWS 1000 PRECEDING) AS rolling_max_acc
    FROM
        (
        SELECT ptid, encid, test_name, result_date, 
        LAG(char_date, 1, 0) OVER (PARTITION BY ptid, test_name 
                                   ORDER BY result_date) as lag_date,
        CASE WHEN lag_date <> 0
            THEN result_date - CAST(lag_date AS DATE FORMAT 'YYYY-MM-DD') 
            ELSE NULL 
            END time_diff,
        test_result,
        -- moving average
        AVG(test_result) OVER (PARTITION BY ptid, test_name 
                               ORDER BY result_date ROWS 1000 PRECEDING) AS rolling_mean,
        -- moving max
        MAX(test_result) OVER (PARTITION BY ptid, test_name 
                               ORDER BY result_date ROWS 1000 PRECEDING) AS rolling_max,
        -- difference 
        LAG(test_result, 1, 0) OVER (PARTITION BY ptid, test_name ORDER BY result_date) AS lag_value,
        -- calculate acceleration for time_diff not equal to 0 (labs on same day)
        CASE WHEN time_diff <> 0
            THEN (test_result - lag_value)/time_diff
            ELSE NULL END acc_value
        FROM 
            (
            SELECT a.ptid, a.encid, a.test_name, 
                b.first_ibd_date, a.result_date, 
                CAST(a.result_date AS VARCHAR(12)) AS char_date,
                TRYCAST(a.test_result AS FLOAT) AS test_result
            FROM RWD_VDM_OPTUM_EHRIBD.IBD_LABS AS a
            INNER JOIN ibd_flare.ibd_cohort AS b
            ON a.ptid = b.ptid AND a.result_date >= b.first_ibd_date
            WHERE batch_title = 'OPTUM EHR IBD 2019 Apr' 
                AND result_date IS NOT NULL
                AND encid IS NOT NULL
                AND value_within_range = 'Y'
                AND test_name IN (
                    {% for lab in labs %}
                        {% if loop.first == True %}
                        '{{ lab }}'
                        {% else %}
                        , '{{ lab }}'
                        {% endif %}
                    {% endfor %}
                )
            ) AS temp 
        ) AS temp2
    )
WITH DATA
ON COMMIT PRESERVE ROWS;