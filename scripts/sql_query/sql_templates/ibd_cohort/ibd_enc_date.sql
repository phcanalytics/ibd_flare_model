CREATE VOLATILE TABLE ibd_enc_date AS
	(
	SELECT a.ptid, a.encid, a.uc_count, a.cd_count, b.interaction_type,
		b.interaction_date
	FROM ibd_enc_count AS a
	LEFT JOIN RWD_VDM_OPTUM_EHRIBD.IBD_ENCOUNTER AS b
	ON (a.encid = b.encid)
    WHERE batch_title = 'OPTUM EHR IBD 2019 Apr'  
	)
WITH DATA
ON COMMIT PRESERVE ROWS;
