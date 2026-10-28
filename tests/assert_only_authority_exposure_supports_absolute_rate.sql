select *
from {{ ref('mart_exposure_coverage') }}
where supports_absolute_rate != (scenario_key = 'la_vehicle_miles')
