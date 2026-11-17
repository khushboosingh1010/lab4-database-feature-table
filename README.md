# Lab 4: Database-Driven Feature Table

Khushboo Singh — PUBH 6854

## Purpose

In this lab, I used SQL and Python to organize the supplied TCGA lung adenocarcinoma database into one table with one row per patient. SQL connected the tables and counted mutation records for five genes. Python/pandas turned those counts into separate columns.

The final table contains 566 patients and 11 columns. The purpose was to prepare a dataset for analysis; I did not perform statistical significance tests.


## How to run the code

From the project folder, install the required package and run the script:

```bash
python -m pip install -r requirements.txt
python build_features.py
```

Alternatively, create and activate the supplied Conda environment:

```bash
conda env create -f environment.yml
conda activate lab4-singh
python build_features.py
```

If the environment already exists, activate it without creating it again.

The script reads `data/cohort.db` and rebuilds the files in `outputs`. To specify different locations:

```bash
python build_features.py --db /path/to/cohort.db --out outputs
```

The project uses the instructor-provided database containing 566 patients. Required packages are listed in requirements.txt.

## Project files

| File | What it contains |
|---|---|
| `build_features.py` | SQL queries, Python transformations, validation checks, and output generation |
| `data/cohort.db` | The unchanged database supplied for the lab |
| `outputs/feature_table.tsv` | The final table with one row per patient |
| `outputs/gene_counts_long.tsv` | Mutation counts for each patient and target gene |
| `outputs/patients_by_site_stage.tsv` | Patient counts grouped by tissue source site and stage |
| `outputs/data_dictionary.tsv` | Definitions, units, sources, and missing-value coding for the final columns |
| `outputs/schema_inspection.md` | Database tables, columns, and keys |
| `outputs/validation_report.md` | Row-count checks, missing values, and verification results |
| `outputs/patient_checks.tsv` | Comparisons between selected patients’ raw records and final counts |
| `outputs/checked_patient_raw_mutations.tsv` | Raw mutation records used in those comparisons |
| `outputs/patients_without_mutation_records.tsv` | The four patients whose samples have no mutation records |
| `SOURCE.md` | Data source and limitations |
| `AI_USAGE.md` | Details of AI assistance and verification |
| `START_HERE.md` | A guide to reviewing and submitting the project |

## Task 1: Understanding the database

I ran checks to see how many records were in each table and how the tables connected. The script also inspects the columns and keys using SQLite PRAGMA commands.

“Grain” means what one row represents.

| Table | Number of rows | What one row represents | Primary key |
|---|---:|---|---|
| patients | 566 | One patient | patient_id |
| samples | 566 | One tumor sample | sample_id |
| mutations | 200789 | One recorded mutation in a sample | mutation_id |
| genes | 17756 | One gene | gene_symbol |

The columns in each table are:

- **patients:** patient_id, sex, age_at_diagnosis, stage, vital_status, followup_months.
- **samples:** sample_id, patient_id, tissue_source_site, tmb_nonsynonymous, aneuploidy_score, msi_mantis_score.
- **mutations:** mutation_id, sample_id, gene_symbol, variant_classification, variant_type, protein_change, chromosome, start_pos, end_pos, t_ref_count, t_alt_count.
- **genes:** gene_symbol, entrez_gene_id, chromosome.

The tables connect through these foreign keys:

- `samples.patient_id` connects to `patients.patient_id`.
- `mutations.sample_id` connects to `samples.sample_id`.
- `mutations.gene_symbol` connects to `genes.gene_symbol`.

The database allows for multiple samples per patient but this set has just one for each. Samples link to mutations and four of them ended up with nothing at all. It seems like that was the case here.

Foreign key checks passed without any issues. There is more gene info in a separate table but the query skips joining it since the symbols for those five genes are right there in the mutations data already. Maybe that keeps things simpler.

## Tasks 2 and 3: Building the patient table

### Query 1: Mutation counts

The first query counts non-Silent mutation records for five genes:

- TP53
- KRAS
- EGFR
- STK11
- KEAP1

The query pulls every patient along with the five target genes from the start. Left joins keep patients included even when mutations do not match up for them. 

It seems the gene and classification conditions sit inside the joins rather than elsewhere. They count on the mutation id field to grab only actual records. Counting everything instead would pick up those empty rows from the join as if they counted for something.

The included classifications are:

- Frame_Shift_Del
- Frame_Shift_Ins
- In_Frame_Del
- In_Frame_Ins
- Missense_Mutation
- Nonsense_Mutation
- Nonstop_Mutation
- Splice_Site
- Translation_Start_Site

Silent mutations are excluded. No mutation classifications are missing in this database. The supplied database’s exclusion of noncoding categories is described in `SOURCE.md`.

The SQL result has one row per patient and target gene. Python/pandas then pivots these results into five separate gene-count columns and merges them with the patient information.

### Query 2: Patients by site and stage

The second query groups patients by tissue source site and cancer stage. It counts distinct patient IDs within each group.

Missing stages are retained, and the original stage labels are kept.

### Checking the number of rows

When I ran the script, the expected and actual row counts matched:

| Check | Expected | Actual |
|---|---:|---:|
| Starting patients | 566 | 566 |
| Patient/sample LEFT JOIN | 566 | 566 |
| Patient/gene summary | 566 × 5 = 2830 | 2830 |
| Observed site/stage groups | 142 | 142 |
| Final patient table | 566 | 566 |

The 142 site/stage groups represent combinations that actually occur in the data. The patient counts across these groups add up to 566.

The final merge checks that each patient appears once and that the set of patient IDs has not changed.

## Task 4: Handling missing data

I kept patients with missing clinical information in the final table. Missing values were not filled in with guesses.

| Clinical field | Missing values |
|---|---:|
| Sex | 52 |
| Age at diagnosis | 71 |
| Stage | 54 |
| Tissue source site | 0 |
| TMB | 0 |

Missing clinical values are written as `NA` in the output table.

Each of the five gene columns consists of integer values. “0” value means that there were no non-Silent mutations recorded for that patient and gene.

There are four samples without any mutations registered. Their gene column is also set to “0”. It doesn’t guarantee the biological normality of the genes or the completeness of sequencing. There is no assay-completeness field in the database.

A zero mutation count and an unknown clinical value therefore have different meanings.

## How I checked the results

When I ran python build_features.py on my Mac, I found out that the validation checks indicated that there were 566 patients in the final table.

The TP53 record for the patient 'TCGA-17-Z023' had one Nonsense Mutation and one Silent mutation. Since the Silent mutations were excluded from consideration, I was expecting that the value of 'TP53_count' would be 1.


The script additionally compares all 2830 patient/gene counts with a separate pandas aggregation of the raw mutation records. All counts matched.



## Task 5: Data dictionary and source

The data dictionary is saved as `outputs/data_dictionary.tsv`. It explains all 11 columns in the final table, including their meanings, units, sources, and missing-value coding.

Data provenance and limitations are documented in `SOURCE.md`. These data are used for a teaching exercise, and the results should not be treated as validated clinical findings.

## AI assistance


I used ChatGPT for support with SQL queries, Python code, and troubleshooting. I set up the environment, ran the script on my Mac, and reviewed the validation output. I also checked patient TCGA-17-Z023’s original TP53 records and confirmed that excluding the Silent mutation gave a final count of 1.

More details about the assistance and checks are included in AI_USAGE.md.