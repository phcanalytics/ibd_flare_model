/* Creates a temporary table that identifies IBD cohort to include
based on having at leave 50% of lab measurements. */
CREATE VOLATILE TABLE ptid_lab_inclusion AS
    (
    SELECT
        ptid, 
        (
        -- loop to add up a flag for at least 1 lab value
        {% for var in var_name_list %}
            {% if loop.first == True %}
            {{ var }}_flag
            {% else %}
             + {{ var }}_flag
            {% endif %}
        {% endfor %}
        ) AS labs_measured_at_least_once,
        (labs_measured_at_least_once*100.0/ {{ labs_measured }}) AS perc_labs 
    FROM
        (
        SELECT 
            ptid
            {% for var in var_name_list %} 
            , CASE WHEN COUNT( {{ var }}_mean_6mo ) > 0
                THEN 1 ELSE 0 END {{ var }}_flag
            {% endfor %}
        FROM labs_6mo
        GROUP BY ptid
        ) AS temp
    WHERE perc_labs >= 50.0
    )
WITH DATA
ON COMMIT PRESERVE ROWS;