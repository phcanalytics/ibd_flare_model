/* Creates and counts up patients with at least one lab in
the six month period. This is calculated for only patients with at
least 50% of the labs measured (inclusion criteria). */
CREATE VOLATILE TABLE ptids_w_labs AS
    (
    SELECT 
        COUNT(ptid) AS n_unique_ptid,
        SUM(n_vis) AS n_vis
        {% for var in var_name_list %} 
        , SUM( {{ var }}_flag)*100.0/n_unique_ptid AS {{ var }}
        {% endfor %}
    FROM
        (
        SELECT 
            ptid,
            COUNT(*) AS n_vis
            {% for var in var_name_list %} 
            , CASE WHEN COUNT( {{ var }}_mean_6mo ) > 0
                THEN 1 ELSE 0 END {{ var }}_flag
            {% endfor %}
        FROM 
            (
            SELECT b.*
            FROM ptid_lab_inclusion AS a
            LEFT JOIN labs_6mo AS b
            ON (a.ptid = b.ptid)
            ) AS temp
        GROUP BY ptid
        ) AS temp2 
    )
WITH DATA
ON COMMIT PRESERVE ROWS;