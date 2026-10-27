// 1. Create a Text parameter named pProjectRoot.
// Example value: C:\Users\your-name\Documents\project8
// 2. Create one blank query per table and paste the matching expression.

// Query name: fact_collision
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\fact_collision.parquet"))
in
    Source

// Query name: fact_local_authority_year_risk
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\fact_local_authority_year_risk.parquet"))
in
    Source

// Query name: fact_exposure_sensitivity
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\fact_exposure_sensitivity.parquet"))
in
    Source

// Query name: dim_date
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\dim_date.parquet"))
in
    Source

// Query name: dim_year
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\dim_year.parquet"))
in
    Source

// Query name: dim_lsoa
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\dim_lsoa.parquet"))
in
    Source

// Query name: dim_local_authority
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\dim_local_authority.parquet"))
in
    Source

// Query name: dim_exposure_scenario
let
    Source = Parquet.Document(File.Contents(pProjectRoot & "\data\powerbi\dim_exposure_scenario.parquet"))
in
    Source
