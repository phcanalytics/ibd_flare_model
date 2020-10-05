/* Creates temp table for immunosuppresive medication date windows of use  */ 
CREATE VOLATILE TABLE immuno_med_date_window AS
        (
        SELECT a.ptid, MIN(a.immuno_med_date) AS first_immuno_med_date,
        	MAX(a.immuno_med_date) AS last_immuno_med_date,
            COUNT(a.generic_desc) AS immuno_med_n
        FROM 
            (
            -- pull from administration table
            SELECT ptid, admin_date AS immuno_med_date, generic_desc
            FROM RWD_VDM_OPTUM_EHRIBD.IBD_MED_ADMINISTRATIONS
            WHERE batch_title = 'OPTUM EHR IBD 2019 Apr' AND 
                (generic_desc IN ('MERCAPTOPURINE',
                                  'AZATHIOPRINE', 
                                  'METHOTREXATE',
                                  'ADALIMUMAB',
                                  'CERTOLIZUMAB',
                                  'GOLIMUMAB'))
            UNION ALL
            -- append rx table
            SELECT ptid, rxdate AS immono_med_date, generic_desc
            FROM RWD_VDM_OPTUM_EHRIBD.IBD_PRESCRIPTIONS
            WHERE batch_title = 'OPTUM EHR IBD 2019 Apr' AND 
                (generic_desc IN ('MERCAPTOPURINE',
                                  'AZATHIOPRINE', 
                                  'METHOTREXATE',
                                  'ADALIMUMAB',
                                  'CERTOLIZUMAB',
                                  'GOLIMUMAB',
                                  'INFLIXIMAB'))
            ) AS a
        INNER JOIN ibd_flare.ibd_cohort AS b
        ON a.ptid = b.ptid  
        GROUP BY a.ptid
        WHERE a.immuno_med_date IS NOT NULL
        ) 
 WITH DATA 
 ON COMMIT PRESERVE ROWS;  