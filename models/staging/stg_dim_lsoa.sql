select *
from read_parquet('{{ var("powerbi_dir", "data/powerbi") }}/dim_lsoa.parquet')
