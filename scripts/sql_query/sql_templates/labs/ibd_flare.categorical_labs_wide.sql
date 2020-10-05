/* This sql template creates a volatile table that finds each of the 
lab values of interest within 7 days of a visit and calculates the max
value */
CREATE TABLE ibd_flare.categorical_labs_wide AS
    (
    SELECT ptid, result_date AS visit_date
        {% for lab, var in labs_zip %}    
        -- abnormal flag baseline value
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN test_abnormal
              ELSE NULL END) AS {{ var }}_abnorm_base
        -- test_ordinal baseline value
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN test_ordinal
              ELSE NULL END) AS {{ var }}_ordinal_base
        -- historic abnormal labs
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN test_abnormal_past 
              ELSE NULL END) AS {{ var }}_abnorm_past
        -- historic abnormal labs
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN test_abnormal_past_sum 
              ELSE NULL END) AS {{ var }}_abnorm_past_sum
        {% endfor %}
    FROM categorical_labs
    GROUP BY ptid, result_date
    )
WITH DATA;
