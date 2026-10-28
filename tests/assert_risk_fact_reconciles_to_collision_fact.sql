select 1
where (select sum(collisions) from {{ ref('stg_fact_local_authority_year_risk') }})
   != (select count(*) from {{ ref('stg_fact_collision') }})
