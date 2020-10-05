CREATE VOLATILE TABLE physical_encounters AS
    (
    SELECT a.ptid, a.visitid, a.encid, 
        a.interaction_type, a.interaction_date, a.academic_community_flag,
        DENSE_RANK() OVER (PARTITION BY a.ptid ORDER BY a.interaction_date) AS visit_n
    FROM
        (
        SELECT ptid, visitid, encid, interaction_type, 
            interaction_date, academic_community_flag,
            -- Create categorical variable of outpatient, inpatient, other
            CASE WHEN interaction_type IN ('Ambulatory patient services', 
                                       'Day surgery patient', 
                                       'Office or clinic patient',
                                       'Urgent care')
				THEN 'outpatient'
                    WHEN interaction_type IN ('Inpatient', 
                                      'Observation patient', 
                                      'Emergency patient')
				THEN 'inpatient'
			ELSE 'other' END service_place
        FROM RWD_VDM_OPTUM_EHRIBD.IBD_ENCOUNTER
        -- Limit to interaction types of inpatient or outpatient
        WHERE service_place <> 'other' AND encid IS NOT NULL AND 
            batch_title = 'OPTUM EHR IBD 2019 Apr'
        ) AS a
    INNER JOIN ibd_flare.ibd_cohort AS b
    ON a.ptid = b.ptid
    )
WITH DATA
ON COMMIT PRESERVE ROWS;