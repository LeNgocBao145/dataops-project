{% test positive_values(model, column_name, allow_zero=false) %}
{#
    Custom generic test: validates that numeric values in column_name are strictly positive (> 0)
    or non-negative (>= 0) when allow_zero=true.
#}

SELECT
    {{ column_name }} AS invalid_value
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
  AND {% if allow_zero %}
      {{ column_name }} < 0
  {% else %}
      {{ column_name }} <= 0
  {% endif %}

{% endtest %}
