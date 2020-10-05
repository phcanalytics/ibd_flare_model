/* This sql template creates a volatile table that finds each of the 
lab values of interest within 7 days of a visit and calculates the max
value */
CREATE TABLE ibd_flare.labs_wide AS
    (
    SELECT ptid, result_date AS visit_date
        -- deduplicating labs by taking the max value on the same dates
        {% for lab, var in labs_zip %}    
        -- baseline value
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN test_result 
              ELSE NULL END) AS {{ var }}_base
        -- rolling mean
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN rolling_mean 
              ELSE NULL END) AS {{ var }}_mean
        -- rolling max
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN rolling_max 
              ELSE NULL END) AS {{ var }}_max
        -- rolling mean of acceleration
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN rolling_mean_acc 
              ELSE NULL END) AS {{ var }}_mean_acc
        -- rolling max of acceleration
        , MAX(CASE WHEN test_name = '{{ lab }}'
              THEN rolling_max_acc 
              ELSE NULL END) AS {{ var }}_max_acc
        {% endfor %}
    FROM longitudinal_labs
    GROUP BY ptid, result_date
    )
WITH DATA;
