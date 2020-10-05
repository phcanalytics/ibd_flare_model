/* Finds inpatient or ER IBD flare events that are at least 90 days apart*/
CREATE VOLATILE TABLE inpat_flare AS 
	(	
	SELECT ptid, interaction_date as visit_date,
		interaction_type, 'flare_inpat' as flare_cat
	FROM
		(
		SELECT ptid, uc_count, cd_count, interaction_date, 
			-- cast date to specific format in ordr to use lag function
			CAST(interaction_date AS DATE FORMAT 'YYYY-MM-DD') AS format_date,
			-- lag function to find last date
			LAG(format_date) OVER (PARTITION BY ptid ORDER BY interaction_date) AS lag_date,
			-- calculate difference since last date; first inpatient observations are NULL
			CASE WHEN lag_date IS NOT NULL
				THEN interaction_date - CAST(lag_date AS DATE FORMAT 'YYYY-MM-DD')
				ELSE NULL END date_diff,
			interaction_type
		FROM 
			(
			SELECT ptid, uc_count, cd_count, interaction_date, interaction_type
			FROM ibd_pos
			-- limit to inpatient or ER visits
			WHERE interaction_type IN ('Inpatient', 'Emergency patient')
			) AS temp
		) AS temp2 
		-- keep first inpatient/er vists or flares 90 days apart (excludes sequential events)
	WHERE (date_diff >= 90 OR date_diff IS NULL)
	)
WITH DATA 
ON COMMIT PRESERVE ROWS;