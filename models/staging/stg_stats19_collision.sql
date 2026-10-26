select collision_index, collision_year::integer as collision_year,
  to_date(date, 'DD/MM/YYYY') as collision_date,
  longitude::double precision, latitude::double precision,
  nullif(local_authority_highway, '-1') as local_authority_highway,
  nullif(local_authority_highway_current, '-1') as local_authority_highway_current,
  nullif(lsoa_of_accident_location, '-1') as lsoa_code,
  nullif(collision_severity::integer, -1) as collision_severity,
  case when collision_severity::integer = -1 then 'unknown' end as collision_severity_missing_reason,
  nullif(speed_limit::integer, -1) as speed_limit,
  case when speed_limit::integer = -1 then 'unknown' end as speed_limit_missing_reason
from {{ source('raw', 'stats19_collision') }}
