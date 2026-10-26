select collision_year, local_authority_highway_current,
  count(*) as collisions,
  count(*) filter (where collision_severity in (1,2)) as fatal_or_serious,
  max(annual_vehicle_miles) as annual_vehicle_miles,
  count(*) * 1e9 / nullif(max(annual_vehicle_miles), 0) as collisions_per_billion_vehicle_miles
from {{ ref('int_collision_context') }}
group by 1,2
