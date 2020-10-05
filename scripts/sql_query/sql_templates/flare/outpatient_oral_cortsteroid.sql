/* Find outpatient corticosteroids */
CREATE VOLATILE TABLE outpatient_oral_cortsteroid AS
    (
    SELECT a.ptid, a.rxdate, a.day_supply_criteria,
    	'outpat_corticosteroid_flare' AS flare_cat
    FROM 
    	(
	    SELECT ptid, rxdate, day_supply_criteria, COUNT(*) AS n_cortsteroid_outpat
	    FROM
	        (
	        SELECT ptid, rxdate, drug_name, ndc, ndc_source, route, quantity_per_fill,
	            num_refills, days_supply, generic_desc, drug_class,
	            CASE WHEN LOWER(generic_desc) IN 
	            ('prednisone', 'methylprednisolone', 'hydrocortisone',
	             'cortisone', 'tixocortol pivalate', 'prednisolone', 'budesonide',
	             'pivalone', 'methylprednisone')
	            -- Required oral route
	            AND route = 'Oral'
	            THEN 1 ELSE 0 END cortsteroid_flag,
	            CASE WHEN days_supply >= 7 
	                        THEN 'yes' ELSE 'no' END day_supply_criteria
	        FROM RWD_VDM_OPTUM_EHRIBD.IBD_PRESCRIPTIONS
	        WHERE cortsteroid_flag = 1 
	            AND batch_title = 'OPTUM EHR IBD 2019 Apr'
	            -- inclusion criteria of have to have days_supply 7 or more days and not medrol
	            AND drug_name NOT LIKE '%MEDROL%'
	        ) AS temp
	    GROUP BY ptid, rxdate, day_supply_criteria
    	) AS a 
    INNER JOIN ibd_flare.ibd_cohort AS b 
    ON a.ptid = b.ptid
    )
WITH DATA
ON COMMIT PRESERVE ROWS
;