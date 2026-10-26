select lsoa_code, lsoa_name, lad_code_2024, lad_name_2024,
  imd_score::double precision, imd_rank::integer, imd_decile::integer,
  population_mid_2022::integer
from {{ source('raw', 'iod2025_lsoa') }}
