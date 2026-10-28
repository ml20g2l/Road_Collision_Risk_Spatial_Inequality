select
  collision_year,
  sum(collisions) as collisions,
  sum(raw_ksi) as raw_ksi,
  sum(adjusted_expected_ksi) as adjusted_expected_ksi,
  sum(case when exposure_available then annual_vehicle_miles else 0 end) as annual_vehicle_miles,
  sum(case when exposure_available then raw_ksi else 0 end)
    / nullif(sum(case when exposure_available then annual_vehicle_miles else 0 end), 0) * 1000000000
    as raw_ksi_per_billion_vehicle_miles,
  sum(case when exposure_available then adjusted_expected_ksi else 0 end)
    / nullif(sum(case when exposure_available then annual_vehicle_miles else 0 end), 0) * 1000000000
    as adjusted_ksi_per_billion_vehicle_miles
from {{ ref('stg_fact_local_authority_year_risk') }}
group by collision_year
