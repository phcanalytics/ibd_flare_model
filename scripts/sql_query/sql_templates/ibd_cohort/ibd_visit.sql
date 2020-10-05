CREATE VOLATILE TABLE ibd_visit AS
	(
	SELECT ptid, encid, uc_count, cd_count, interaction_type,
		interaction_date, service_place, ic_flag,
		-- Count of number of encounters
		ROW_NUMBER() OVER(PARTITION BY ptid ORDER BY interaction_date) AS encounter_n,
		-- Count of number of ibd visits (assuming enounters on same date count as one visit)
		DENSE_RANK() OVER(PARTITION BY ptid ORDER BY interaction_date) AS ibd_visit_n,
		-- Flag for outpatient/inpatient/er visit defined by Diana and Ryan
		CASE WHEN service_place = 'outpatient'
			THEN 1 ELSE 0 END outpatient_flag,
		CASE WHEN service_place = 'inpatient'
			THEN 1 ELSE 0 END inpat_er_obs_flag,
		CASE WHEN interaction_type = 'Inpatient'
			THEN 1 ELSE 0 END inpatient_flag,
		CASE WHEN interaction_type = 'Emergency patient'
			THEN 1 ELSE 0 END er_flag
	FROM ibd_pos
	)
WITH DATA
ON COMMIT PRESERVE ROWS;
