{% test date_order(model, start_date_column, end_date_column, allow_equal=true) %}
{#
    Custom generic test: validates chronological ordering between two date columns
    (end_date_column >= start_date_column, or > when allow_equal=false).
#}

SELECT
    {{ start_date_column }} AS start_date,
    {{ end_date_column }} AS end_date
FROM {{ model }}
WHERE {{ start_date_column }} IS NOT NULL
  AND {{ end_date_column }} IS NOT NULL
  AND {% if allow_equal %}
      {{ end_date_column }} < {{ start_date_column }}
  {% else %}
      {{ end_date_column }} <= {{ start_date_column }}
  {% endif %}

{% endtest %}
