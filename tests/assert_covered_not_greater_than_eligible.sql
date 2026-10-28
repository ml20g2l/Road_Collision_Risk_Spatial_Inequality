select *
from {{ ref('mart_exposure_coverage') }}
where covered_collisions > eligible_collisions
