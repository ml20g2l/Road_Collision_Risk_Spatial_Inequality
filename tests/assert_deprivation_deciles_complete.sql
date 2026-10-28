select expected.imd_decile
from range(1, 11) expected(imd_decile)
left join {{ ref('mart_deprivation_inequality') }} actual using (imd_decile)
where actual.imd_decile is null
