with collision_summary as (
  select
    imd_decile,
    count(*) as collisions,
    sum(cast(is_fatal_or_serious_raw as integer)) as raw_ksi,
    sum(expected_adjusted_ksi) as adjusted_expected_ksi
  from {{ ref('stg_fact_collision') }}
  where imd_decile between 1 and 10
  group by imd_decile
),
population as (
  select imd_decile, sum(population_mid_2022) as population_mid_2022
  from {{ ref('stg_dim_lsoa') }}
  where imd_decile between 1 and 10
  group by imd_decile
)
select
  c.*,
  p.population_mid_2022,
  c.collisions / nullif(p.population_mid_2022 * 5.0, 0) * 100000 as collisions_per_100k_resident_years,
  c.adjusted_expected_ksi / nullif(c.collisions, 0) * 100 as adjusted_ksi_per_100_collisions
from collision_summary c
join population p using (imd_decile)
