select *
from read_parquet('{{ var("powerbi_dir", "data/powerbi") }}/fact_collision.parquet')
