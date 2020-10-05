/* Script to count up previous flare sum  */
CREATE VOLATILE TABLE previous_flare_sum AS
    (
    SELECT ptid, flare_date, inpat_flare, interaction_type, 
    	steroid_flare, day_supply_criteria, flare_cat, flare_v1, flare_v2,
 		-- previous flare sum of flare version 1; intermediate
 		SUM(flare_v1) OVER 
 			(PARTITION BY ptid ORDER BY 
 			flare_date ROWS 1000 PRECEDING) AS flare_v1_n,
  		-- previous flare sum of flare version 2; intermediate
 		SUM(flare_v2) OVER 
 			(PARTITION BY ptid ORDER BY 
 			flare_date ROWS 1000 PRECEDING) AS flare_v2_n		
	FROM ibd_flare.flares
    )
WITH DATA 
ON COMMIT PRESERVE ROWS;
