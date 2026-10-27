# Project Learning Guide

## Road Collision Risk & Spatial Inequality

This guide explains the knowledge behind the project. It also explains what the project proves, what it does not prove, and how to reuse the work.

## 1. Why this project exists

Road collision counts do not answer every safety question.

A place can have many collisions because it has high traffic volume. Another place can have fewer collisions but a high rate of severe outcomes after traffic exposure is taken into account. A deprived community can also have a high collision burden relative to its resident population.

These are different problems. They can require different actions.

The project separates three questions:

1. Where do collisions occur?
2. Where is killed or seriously injured risk high after adjustment for vehicle miles?
3. Which communities have a high resident-normalised collision burden?

The project also shows the limits of the data. It does not present a weak traffic match as a precise road-link risk measure.

## 2. What the project contains

The project covers the full analytics workflow:

1. Define the decision questions.
2. Audit official source data.
3. Define grain and keys.
4. Clean and join collision, geography, deprivation, and traffic data.
5. Build analytical marts.
6. Test data quality and sensitivity.
7. Define measures in Data Analysis Expressions (DAX).
8. Build a Power BI semantic model.
9. Design a four-page dashboard.
10. Publish reproducible code and documentation in GitHub.

This scope makes the project more than a chart exercise. It connects data engineering, analysis, spatial reasoning, semantic modelling, and communication.

## 3. Core data concepts

### 3.1 Grain

Grain defines what one row represents.

- `fact_collision`: one row for one collision.
- `fact_local_authority_year_risk`: one row for one local authority and one year.
- `fact_exposure_sensitivity`: one row for one year and one exposure scenario.

A clear grain prevents duplicate counts and invalid joins.

### 3.2 Keys

A key identifies a row or connects tables.

- `collision_index` identifies one collision.
- `date_key` connects a collision to the date dimension.
- `collision_year` connects facts to the year dimension.
- `lsoa_code_2021` connects a collision to deprivation and population data.
- `local_authority_highway_current` connects a collision and a risk record to a local authority.
- `scenario_key` identifies one exposure scenario.

### 3.3 Fact and dimension tables

Fact tables store events or measurements. Dimension tables store descriptive context.

The model uses a star-schema pattern. Dimensions filter facts through one-to-many relationships. The model uses single-direction filters to reduce ambiguity.

This design improves measure consistency and report performance.

## 4. Important analytical concepts

### 4.1 Counts and rates answer different questions

A collision count measures volume. It does not measure risk after exposure.

A rate uses a denominator. The denominator defines the meaning of the result.

Examples:

- Collisions per 100,000 resident-years measure community burden.
- Killed or seriously injured outcomes per billion vehicle miles measure road risk after traffic exposure.
- Adjusted KSI per 100 collisions measures conditional severity after a collision occurs.

These measures must not be treated as substitutes for each other.

### 4.2 KSI

KSI means killed or seriously injured.

Raw KSI uses the reported collision severity. Adjusted expected KSI uses an injury-based adjustment. The dashboard shows both measures. It does not hide the original reported value.

The adjustment increased the national KSI rate by 6.0% in 2021 and 2.1% in 2025. This result shows that measurement adjustment can change the level of a metric over time.

### 4.3 Exposure-adjusted risk

Traffic volume changes the opportunity for collisions. Vehicle miles provide an exposure denominator.

The project calculates:

`KSI rate = KSI / annual vehicle miles x 1,000,000,000`

This rate supports comparisons between local authorities with different traffic volumes.

The measure is still descriptive. It does not prove why one authority has a higher rate.

### 4.4 Resident-normalised burden

The deprivation analysis uses resident population. It does not use traffic exposure.

The measure answers this question:

`How many collisions occur relative to the number of people who live in the area?`

It does not answer this question:

`How risky is each mile of road travel?`

This difference is one of the most important lessons in the project.

### 4.5 Deprivation deciles

The English Index of Multiple Deprivation assigns small areas to deciles.

- Decile 1 is the most deprived group.
- Decile 10 is the least deprived group.

The project found 187.7 collisions per 100,000 residents per year in the most deprived decile. It found 92.5 in the least deprived decile. The five-year ratio was 2.03.

This is an association. The result does not prove that deprivation causes collisions.

### 4.6 Conditional severity

Conditional severity measures the expected KSI outcome after a collision occurs.

In 2025, rural collisions had 31.7 adjusted expected KSI outcomes per 100 collisions. Urban collisions had 24.3.

Across 2021 to 2025, the measure was 20.4 on 20 mph roads and 36.5 on 60 mph roads. The 70 mph value was lower than the 60 mph value.

Speed limit alone is not a causal explanation. Road design, traffic separation, road class, junction context, and road-user mix can also affect severity.

### 4.7 Spatial joins

Official datasets can use different geographic versions.

The project converts historic Lower Layer Super Output Area codes to 2021 geography. It uses the Office for National Statistics best-fit lookup where direct matching is not possible.

This process prevents false missing values and invalid deprivation joins.

### 4.8 Sensitivity analysis

A sensitivity analysis tests whether a result changes when an assumption or method changes.

The project tests Annual Average Daily Flow (AADF) point matches at different distance thresholds. Only about 11% of eligible numbered-road collisions have a same-year and same-road AADF point within 100 metres.

This coverage is too low for a national absolute road-link risk measure. The project uses AADF point matches only as a diagnostic.

This is a useful analytical decision. A weak denominator is not better than an explicit limitation.

### 4.9 Rank correlation

The project compares raw and adjusted local-authority rankings with Spearman rank correlation.

The 2025 correlation was 0.991. The adjustment changed metric levels more than it changed the broad spatial order.

A high correlation does not mean that the measures are identical. It means that their ranking order is very similar.

### 4.10 Association and causality

The project reports observed patterns. It does not estimate causal effects.

A dashboard can show where to investigate. It cannot prove which intervention will cause an improvement.

A causal study would need a stronger design. Examples include a controlled experiment, a natural experiment, a difference-in-differences study, or a matched comparison.

## 5. Tools and why they were used

### Python and pandas

Python performs data ingestion, cleaning, joining, validation, and export. Pandas supports transparent table operations and repeatable calculations.

### Jupyter notebooks

The notebooks record the audit, join checks, sensitivity analysis, and decision findings. They support review and reproducibility.

### SQL and dbt-style models

The SQL models separate staging, intermediate, and mart logic. This structure makes each transformation easier to test and maintain.

### Parquet

Parquet stores typed analytical tables in a compact format. It is faster and smaller than CSV for repeated analytical use.

### Power Query M

Power Query loads the Parquet outputs into Power BI. It also gives each query a controlled name and type structure.

### DAX

DAX defines reusable business measures. It controls aggregation, filter context, ranking, year comparison, and scenario selection.

### Power BI

Power BI provides the semantic model, interactive filters, maps, KPI cards, charts, and narrative panels.

### Git and GitHub

Git records changes. GitHub publishes the code, model definitions, dashboard files, and reproducibility material.

## 6. Power BI concepts to understand

### 6.1 Filter context

A DAX measure calculates a result for the current filter context.

A Year slicer changes the current year. A local-authority category changes the current authority. A visual can also add its own filters.

The same measure can return a national value, a yearly value, or an authority value without a new formula.

### 6.2 Disconnected selector table

The risk metric selector has no relationship to the data model.

A `SWITCH` measure reads the selected option and returns the raw or adjusted risk measure. This pattern supports a user-controlled metric without an ambiguous relationship.

### 6.3 Weighted rates

The project calculates total numerators divided by total denominators.

It does not calculate an average of local-authority rates. An average of rates can give the wrong national result because authorities have different traffic volumes.

### 6.4 Visual interactions

Not every slicer must filter every visual.

For example, an annual trend can keep all five years while KPI cards respond to the selected year. The report uses interaction controls to keep the correct analytical context.

### 6.5 Guardrail measures

Guardrail measures show whether the data is suitable for the main analysis.

Examples include traffic coverage, geographic join coverage, AADF match coverage, and raw-versus-adjusted rank correlation.

These measures make analytical confidence visible beside the result.

## 7. Main findings

- The repository contains 513,801 collision records for 2021 to 2025.
- The most deprived decile had about twice the resident-normalised collision burden of the least deprived decile.
- The deprivation gap was stronger in collision occurrence than in conditional severity.
- Rural collisions had more severe expected outcomes than urban collisions in 2025.
- Conditional severity was highest on 60 mph roads in the selected speed-limit comparison.
- Injury-based adjustment changed KSI levels, but it did not materially change the 2025 local-authority ranking.
- Local-authority vehicle-mile coverage was approximately 99.98%.
- The 100-metre AADF match covered only about 11% of eligible numbered-road collisions.

## 8. What this project teaches

### Technical lessons

- Define grain before joins and measures.
- Test relationship cardinality before dashboard work.
- Use the correct denominator for each question.
- Recalculate rates from total numerators and denominators.
- Keep original and adjusted metrics together.
- Test geographic crosswalks and unmatched records.
- Separate production measures from sensitivity diagnostics.
- Put data-quality evidence in the dashboard.
- Design DAX measures for the required filter context.
- Validate important dashboard values outside Power BI.

### Analytical lessons

- A high count is not the same as high risk.
- A resident denominator is not a traffic denominator.
- A ranking can be stable when metric levels change.
- A strong pattern does not prove a cause.
- A limitation can change the correct product decision.
- One dashboard can require more than one intervention path.

### Communication lessons

- A dashboard title must state the analytical question.
- A KPI needs a clear unit and denominator.
- A warning must be close to the affected result.
- A decision signal must explain the next investigation.
- A quality page can increase trust in the other pages.

## 9. How to reuse the work

The same design can support other domains.

### Transport and mobility

- cyclist and pedestrian safety
- public transport incidents
- freight and road-network exposure
- speed-management reviews
- local-authority safety prioritisation

### Public health

- disease burden by deprivation
- emergency attendance rates
- access to health services
- environmental exposure by community

### Insurance and risk

- claims per insured exposure
- severity after an incident
- geographic risk concentration
- model and coverage guardrails

### Operations

- incidents per operating hour
- defects per unit produced
- failures per customer or transaction
- site-level investigation queues

### Product analytics

- events per active user
- conversion rates by segment
- outcome severity after an event
- data-quality coverage beside product KPIs

The reusable pattern is:

`event count + exposure denominator + group inequality + severity + quality guardrail`

## 10. Suitable roles

This project provides evidence for applications to these roles:

- Data Analyst
- Business Intelligence Analyst
- Power BI Developer
- Analytics Engineer
- Geospatial Data Analyst
- Transport Data Analyst
- Road Safety Analyst
- Public Sector Data Analyst
- Public Health Analyst
- Risk Analyst
- Policy Analyst
- Data and Analytics Consultant

The project is especially useful for roles that need SQL, Python, Power BI, data modelling, metric design, spatial analysis, and stakeholder communication.

## 11. Suitable sectors

- transport and mobility
- local and central government
- public health
- urban planning
- infrastructure
- insurance
- consulting
- logistics
- automotive safety
- research and policy

## 12. How to explain the project in an interview

Use this structure:

1. State the decision problem.
2. Explain why collision counts were not sufficient.
3. Explain the three denominators.
4. Describe the geographic and traffic joins.
5. Explain the star schema and DAX measures.
6. Give two or three important findings.
7. Explain the AADF limitation.
8. State how the dashboard supports an investigation, not a causal conclusion.

Example:

> I built an end-to-end road-safety analytics project with official UK data. I separated collision volume, resident-normalised community burden, exposure-adjusted road risk, and conditional severity. I used Python and SQL-style models to build validated marts. I then created a Power BI star schema and a four-page dashboard. The analysis found a 2.03 times deprivation burden gap and higher rural conditional severity. I also found that the AADF point match had low coverage, so I kept it as a sensitivity diagnostic instead of using it as an absolute risk denominator. This decision is important because it prevents a precise dashboard from hiding weak evidence.

## 13. Limits and useful next work

The current project has these limits:

- It is observational.
- Deprivation data covers England, while STATS19 covers Great Britain.
- A local-authority average can hide road-level variation.
- AADF point matching does not represent full road-segment exposure.
- The model does not include detailed road geometry, road-user type, vehicle mix, or intervention history.
- Small-area rates need uncertainty estimates before operational use.

Useful extensions include:

- road-segment geometry matching
- Bayesian or empirical-Bayes rate stabilisation
- confidence intervals for local rates
- pedestrian and cyclist segmentation
- spatial clustering and hotspot analysis
- before-and-after intervention evaluation
- a causal design for specific road-safety policies
- automated data refresh and regression tests

## 14. Final lesson

The main lesson is not how to build a dark Power BI dashboard.

The main lesson is how to connect a decision question to the correct grain, key, denominator, model, validation rule, visual, and limitation.

That connection turns a dashboard into an analytical product.
