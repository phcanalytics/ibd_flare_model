CREATE VOLATILE TABLE visits AS
    (
    SELECT ptid, COUNT(interaction_type) AS n_interaction_type, 
        interaction_date AS visit_date, MAX(visit_n) AS visit_n
    FROM physical_encounters
    GROUP BY ptid, interaction_date
    )
WITH DATA 
ON COMMIT PRESERVE ROWS;