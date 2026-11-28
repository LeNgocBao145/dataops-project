{% test percentage_range(model, column_name, min_value=0, max_value=100) %}
{#
    Custom generic test: validates that a ratio/percentage column stays within [min_value, max_value].
#}

SELECT
    {{ column_name }} AS invalid_percentage
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
  AND (
      {{ column_name }} < {{ min_value }}
      OR {{ column_name }} > {{ max_value }}
  )

{% endtest %}
