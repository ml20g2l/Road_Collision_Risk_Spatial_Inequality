select c.*, coalesce(c.lsoa_code, x.lsoa_code_2021) as lsoa_code_2021,
  case when i_direct.lsoa_code is not null then 'direct_2021_code'
       when x.lsoa_code_2021 is not null then 'ons_best_fit_2011_to_2021'
       else 'unmatched' end as lsoa_mapping_method,
  coalesce(i_direct.imd_score, i_cross.imd_score) as imd_score,
  coalesce(i_direct.imd_rank, i_cross.imd_rank) as imd_rank,
  coalesce(i_direct.imd_decile, i_cross.imd_decile) as imd_decile,
  t.annual_vehicle_miles,
  st_setsrid(st_makepoint(c.longitude, c.latitude), 4326) as collision_geom
from {{ ref('stg_stats19_collision') }} c
left join {{ ref('stg_iod2025_lsoa') }} i_direct using (lsoa_code)
left join {{ ref('stg_ons_lsoa11_lsoa21_best_fit') }} x on c.lsoa_code = x.lsoa_code_2011
left join {{ ref('stg_iod2025_lsoa') }} i_cross on x.lsoa_code_2021 = i_cross.lsoa_code
left join {{ ref('stg_local_authority_traffic') }} t
  on (case c.local_authority_highway when 'E08000038' then 'E08000016' when 'E08000039' then 'E08000019' else c.local_authority_highway end) = t.local_authority_code
 and c.collision_year = t.year
