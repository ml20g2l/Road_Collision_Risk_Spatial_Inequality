# Data Contracts

## Core grains

| Model | Grain | Primary key |
|---|---|---|
| `fact_collision` | One reported collision | `collision_index` |
| `fact_local_authority_year_risk` | One authority and collision year | `local_authority_highway_current`, `collision_year` |
| `fact_exposure_sensitivity` | One exposure scenario and collision year | `scenario_key`, `collision_year` |
| `dim_date` | One calendar date | `date_key` |
| `dim_year` | One collision year | `collision_year` |
| `dim_lsoa` | One 2021 LSOA | `lsoa_code_2021` |
| `dim_local_authority` | One current highway authority | `local_authority_highway_current` |
| `dim_exposure_scenario` | One exposure scenario | `scenario_key` |

## Stable quality rules

- Collision, dimension, and composite fact keys must be unique and not null.
- Collision years must be 2021 to 2025.
- IMD deciles must be 1 to 10 when present.
- English collisions must resolve to an IoD 2025 LSOA after geography conformance.
- Authority traffic coverage must be at least 99.9%.
- Exposure coverage rates must stay between zero and one.
- Covered collisions cannot exceed eligible collisions.
- Only authority-year vehicle miles support an absolute exposure-adjusted rate.
- AADF point matching remains a coverage and sensitivity diagnostic.
- Authority-year collision totals must reconcile to the collision fact.

## Metric rules

`Adjusted expected KSI` equals one for a fatal collision, the injury-based serious probability for a serious collision, and zero for a slight collision.

`Adjusted KSI per billion vehicle miles` divides the sum of adjusted expected KSI by authority-year vehicle miles and multiplies the result by one billion. It is recalculated from additive numerators and denominators rather than averaged across authorities.

`Collision burden per 100,000 resident-years` is a community-burden measure. It must not be described as traffic-exposure-adjusted risk.

## Change control

A source refresh, year extension, geography revision, denominator change, or severity-rule change requires:

1. a source-manifest update;
2. schema and grain validation;
3. join-coverage comparison with the previous build;
4. rerunning pytest and dbt tests;
5. reviewing public metrics and dashboard claims; and
6. documenting any break in comparability.
