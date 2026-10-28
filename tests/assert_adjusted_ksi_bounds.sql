select *
from {{ ref('stg_fact_collision') }}
where expected_adjusted_ksi < 0 or expected_adjusted_ksi > 1
