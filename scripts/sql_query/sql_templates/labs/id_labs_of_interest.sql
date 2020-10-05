/*Script to find labs of interest that have an observed value within 
biologically plausible range and test type not equal to blood gas */
SELECT test_name, test_type, result_unit, 
    value_within_range, COUNT(*)
FROM RWD_VDM_OPTUM_EHRIBD.IBD_LABS 
WHERE batch_title = 'OPTUM EHR IBD 2019 Apr' AND
    value_within_range = 'Y' AND test_type <> 'BLOOD GAS' AND 
    (
    {% for lab in labs %}
        {% if loop.first == True %}
            test_name LIKE '%{{ lab }}%'
            {% else %}
            OR test_name LIKE '%{{ lab }}%'
        {% endif %}
    {% endfor %}
    )
GROUP BY test_name, test_type, result_unit, value_within_range;
