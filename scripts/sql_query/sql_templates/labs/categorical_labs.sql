/* This sql template creates categorical lab values based on the observed lab value
comapred to the listed normal range of the test.

A variable called `test_abnormal` checks if the lab value is within the listed normal range. 
It is coded as follows: abnormal yes=1/no=0 

There is a second variable called `test_ordinal`, which is a categorical
variable labeld as low, normal, high.

These variables are created for each lab of interest for each person in the IBD cohort */
CREATE VOLATILE TABLE categorical_labs AS 
	(
	SELECT 
		ptid, 
		first_ibd_date,
		test_name,
		result_date, 
		n_tests,
		test_result,
		normal_range,
		test_abnormal,
		test_ordinal,
		-- binary any past abnormal test temp variable
	    MAX(test_abnormal) OVER (PARTITION BY ptid, test_name 
	                             ORDER BY result_date ROWS 1000 PRECEDING) AS test_abnormal_past_temp,                 
	    -- number of past abnormal tests temp variable
	    SUM(test_abnormal) OVER (PARTITION BY ptid, test_name 
	                         ORDER BY result_date ROWS 1000 PRECEDING) AS test_abnormal_past_sum_temp,
	    -- correct sum of past lab and past lab if it's the first event
	    CASE WHEN (test_abnormal = 1 AND 
	    		   test_abnormal_past_sum_temp = 1)
	    	THEN test_abnormal_past_temp - 1 
	    	ELSE test_abnormal_past_temp 
	    	END test_abnormal_past, 
	    -- subtract off 1 for those greater than 0
	    CASE WHEN (test_abnormal_past_sum_temp > 0)
	    	THEN test_abnormal_past_sum_temp - 1 
	    	ELSE test_abnormal_past_sum_temp 
	    	END test_abnormal_past_sum     	
	FROM 
		(                         
		SELECT 
			ptid,
			first_ibd_date,
			test_name,
			result_date, 
			COUNT(test_result) AS n_tests,
			-- aggregated on test result date and lab
			-- take the highest lab result
			MAX(test_result) AS test_result, 
			MAX(normal_range) AS normal_range,
			MAX(test_abnormal) AS test_abnormal,
			MAX(test_ordinal) AS test_ordinal                
		FROM
			(
			SELECT a.ptid,
				b.first_ibd_date,
				a.encid, 
				a.test_name, 
				a.result_date,
				TRYCAST(a.test_result AS NUMBER) AS test_result, 
				a.normal_range, 
				-- try to convert the string element from split to number
				TRYCAST(
					-- split string by '-' and take the first number
					-- this is a teradata sql specific function
					STRTOK(a.normal_range, '-', 1) AS NUMBER) AS num_val_1,
					-- split string by '-' and take the second number
					-- this is a teradata sql specific function for string split by delim
				TRYCAST(
					STRTOK(a.normal_range, '-', 2) AS NUMBER) AS num_val_2,
					-- make sure to take the lowest number of the two
				CASE WHEN num_val_1 < num_val_2
					THEN num_val_1 
					ELSE num_val_2 
					END min_range, 
					-- make sure to take the highest number of the two
				CASE WHEN num_val_1 > num_val_2 
					THEN num_val_1 
					ELSE num_val_2 
					END max_range,
				-- class to indicate if lab value is abnormal (does not distinguish low or high)
				CASE WHEN (test_result >= min_range AND test_result <= max_range)
					THEN 0 
				WHEN (test_result > max_range OR test_result < min_range)
					THEN 1
					END test_abnormal,
				-- categorical variable low, normal, high; added a number for easy ordering
				CASE WHEN (test_result >= min_range AND test_result <= max_range)
					THEN '1_normal' 
				WHEN (test_result < min_range)
					THEN '0_low'
				WHEN (test_result > max_range)
					THEN '2_high'
					END test_ordinal
			FROM RWD_VDM_OPTUM_EHRIBD.IBD_LABS AS a
			INNER JOIN ibd_flare.ibd_cohort AS b 
			ON a.ptid = b.ptid AND a.result_date >= b.first_ibd_date
			WHERE batch_title = 'OPTUM EHR IBD 2019 Apr'
				AND result_date IS NOT NULL
			    AND encid IS NOT NULL
			    AND value_within_range = 'Y'
                --jinja template for loop lab names
			    AND test_name IN (
                    {% for lab in labs %}
                        {% if loop.first == True %}
                        '{{ lab }}'
                        {% else %}
                        , '{{ lab }}'
                        {% endif %}
                    {% endfor %}
                )
			) AS temp
		GROUP BY ptid, first_ibd_date, test_name, result_date
		) AS temp2
	)
WITH DATA
ON COMMIT PRESERVE ROWS;