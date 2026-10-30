{#- yyyymmdd integer key for dim_date; null dates stay null. -#}
{% macro date_key(date_column) -%}
    (year({{ date_column }}) * 10000 + month({{ date_column }}) * 100 + day({{ date_column }}))
{%- endmacro %}
