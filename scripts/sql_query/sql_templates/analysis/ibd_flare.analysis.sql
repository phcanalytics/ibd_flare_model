/* keeps only visit/observations with at least 1 lab measured */
CREATE TABLE ibd_flare.analysis AS 
    (
    SELECT *
    FROM flare_predictors
    WHERE 
    {% for lab in labs %}
        {% if loop.first == True %}
            {{ lab }} IS NOT NULL
            {% else %}
            OR {{ lab }} IS NOT NULL
        {% endif %}
    {% endfor %}
    ) 
WITH DATA;