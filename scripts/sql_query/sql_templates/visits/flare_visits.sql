/* Create final visits table with flare events and excluding visits
 that have a corticosteroid without a 7 day supply and no other stricter
 definition of flare present */
CREATE TABLE ibd_flare.flare_visits AS
    (
    SELECT ptid, visit_date, visit_n,
        MIN(flare_date) AS flare_date, MIN(inpat_flare) AS inpat_flare, 
        MIN(interaction_type) AS interaction_type, MIN(steroid_flare) AS steroid_flare,
        MIN(day_supply_criteria) AS day_supply_criteria, MIN(flare_cat) AS flare_cat, 
        MIN(flare_v1) AS flare_v1, MIN(prev_flare_v1_sum) AS prev_flare_v1_sum, 
        MIN(flare_v2) AS flare_v2, MIN(prev_flare_v2_sum) AS prev_flare_v2_sum
    FROM 
    (
    SELECT a.ptid, a.n_interaction_type, a.visit_date, a.visit_n,
     b.flare_date, b.inpat_flare, b.interaction_type, b.steroid_flare, 
     b.day_supply_criteria, b.flare_cat, 
     CASE WHEN b.flare_v1 = 1 
        THEN 1 ELSE 0 END flare_v1,
     CASE WHEN b.flare_v1_n = 1 AND flare_v1 = 1
        THEN 0 
        ELSE MAX(b.flare_v1_n) OVER 
            (PARTITION BY a.ptid ORDER BY 
                a.visit_date ROWS 1000 PRECEDING) END pfv1_sum_int,
     CASE WHEN pfv1_sum_int IS NULL
            THEN 0 
        WHEN b.flare_v1 = 1 AND (pfv1_sum_int = 0 OR pfv1_sum_int IS NULL)
            THEN 0
        WHEN b.flare_v1 = 1 AND pfv1_sum_int > 0
            THEN pfv1_sum_int - 1
            ELSE pfv1_sum_int END prev_flare_v1_sum,
     CASE WHEN b.flare_v2 = 1 
        THEN 1 ELSE 0 END flare_v2,
     -- less strict flare def
     CASE WHEN b.flare_v2_n = 1 AND flare_v2 = 1
        THEN 0 
        ELSE MAX(b.flare_v2_n) OVER 
            (PARTITION BY a.ptid ORDER BY 
                a.visit_date ROWS 1000 PRECEDING) END pfv2_sum_int,
     CASE WHEN pfv2_sum_int IS NULL
            THEN 0 
        WHEN b.flare_v2 = 1 AND (pfv2_sum_int = 0 OR pfv2_sum_int IS NULL)
            THEN 0
        WHEN b.flare_v2 = 1 AND pfv2_sum_int > 0
            THEN pfv2_sum_int - 1
            ELSE pfv2_sum_int END prev_flare_v2_sum
    FROM visits AS a 
    LEFT JOIN previous_flare_sum AS b 
    ON (a.ptid = b.ptid) AND (b.flare_date >= a.visit_date 
                     AND b.flare_date <= a.visit_date + 180)
    ) AS temp
    -- deduping multiple flare events joined to a single visit
    GROUP BY ptid, visit_date, visit_n
    -- excluding visit dates on the same day as flare date for now
    WHERE (visit_date <> flare_date OR flare_date IS NULL) 
    ) 
WITH DATA;