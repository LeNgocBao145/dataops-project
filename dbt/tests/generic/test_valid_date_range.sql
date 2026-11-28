{% test valid_date_range(model, column_name, min_date='2011-01-01', max_date=none) %}
{#
    Custom generic test: validates that date/datetime values fall within [min_date, max_date].
    When max_date is not provided, defaults to GETDATE() (no future dates).
#}

SELECT
    {{ column_name }} AS invalid_date
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
  AND (
      {{ column_name }} < CAST('{{ min_date }}' AS DATE)
      OR {{ column_name }} > {% if max_date is not none %}CAST('{{ max_date }}' AS DATE){% else %}CAST(GETDATE() AS DATE){% endif %}
  )

{% endtest %}
