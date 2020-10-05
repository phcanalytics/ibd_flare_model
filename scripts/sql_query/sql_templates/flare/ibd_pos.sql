CREATE VOLATILE TABLE ibd_pos AS
	(
 	SELECT ptid, encid, uc_count, cd_count, interaction_type, interaction_date,
		-- Create flag to indicate ic
		CASE WHEN (uc_count > 0 AND cd_count > 0)
			THEN 1 ELSE 0 END ic_flag,
		-- Create categorical variable of outpatient, inpatient, other
		CASE WHEN interaction_type IN 
            ('Ambulatory patient services', 
             'Day surgery patient', 
             'Office or clinic patient',
             'Urgent care')
				THEN 'outpatient'
		WHEN interaction_type IN 
            ('Inpatient', 
             'Observation patient', 
             'Emergency patient')
				THEN 'inpatient'
			ELSE 'other' END service_place
	FROM ibd_enc_date
	-- Limit to interaction types of inpatient or outpatient
	WHERE service_place <> 'other' AND encid IS NOT NULL
	)
WITH DATA
ON COMMIT PRESERVE ROWS;