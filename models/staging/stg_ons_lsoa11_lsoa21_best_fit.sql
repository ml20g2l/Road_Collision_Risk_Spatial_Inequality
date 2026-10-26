select "LSOA11CD" as lsoa_code_2011, "LSOA21CD" as lsoa_code_2021
from {{ source('raw', 'ons_lsoa11_lsoa21_best_fit') }}
