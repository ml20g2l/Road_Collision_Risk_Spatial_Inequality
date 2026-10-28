select *
from {{ ref('mart_exposure_coverage') }}
where coverage_rate < 0 or coverage_rate > 1
