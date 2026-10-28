select
  collision_year,
  scenario_key,
  scenario_label,
  covered_collisions,
  eligible_collisions,
  coverage_rate,
  supports_absolute_rate
from {{ ref('stg_fact_exposure_sensitivity') }}
