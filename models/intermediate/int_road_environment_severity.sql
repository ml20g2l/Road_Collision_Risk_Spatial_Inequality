select
  collision_year,
  urban_or_rural_area_label as environment,
  count(*) as collisions,
  sum(expected_adjusted_ksi) as adjusted_expected_ksi,
  sum(expected_adjusted_ksi) / nullif(count(*), 0) * 100 as adjusted_ksi_per_100_collisions
from {{ ref('stg_fact_collision') }}
where urban_or_rural_area_label in ('Urban', 'Rural')
group by collision_year, urban_or_rural_area_label
