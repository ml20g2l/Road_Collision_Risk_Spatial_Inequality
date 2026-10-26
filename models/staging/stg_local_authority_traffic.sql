select local_authority_code, year::integer,
  annual_vehicle_miles::double precision
from {{ source('raw', 'dft_local_authority_traffic') }}
