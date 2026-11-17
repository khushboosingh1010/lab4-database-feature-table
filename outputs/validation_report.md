# Validation results

| Check | Expected | Actual |
|---|---:|---:|
| Patients before joins | 566 | 566 |
| After patient/sample LEFT JOIN | 566 | 566 |
| Query 1 patient/gene groups | 566 × 5 = 2830 | 2830 |
| Query 2 observed site/stage groups | 142 | 142 |
| Sum of Query 2 patient counts | 566 | 566 |
| After merging wide gene counts | 566 | 566 |

Query 1 started with 2830 patient/gene combinations (566 patients × 5 genes). Joining mutation records increased this to 2876 rows because some patients had multiple mutations in a gene. Grouping returned the result to 2830 rows before the Python pivot. All 566 patients were retained.

Query 2 produced 142 site/stage combinations observed in the data, including missing stages. Its patient counts summed to 566.

All expected and actual counts matched.

## Missing values

- patient_id: 0 missing values retained.
- sex: 52 missing values retained.
- age_at_diagnosis: 71 missing values retained.
- stage: 54 missing values retained.
- tissue_source_site: 0 missing values retained.
- tmb_nonsynonymous: 0 missing values retained.

Samples with no mutation records: 4. Their gene counts are 0 (no qualifying recorded call), not a biological wild-type conclusion. IDs are in patients_without_mutation_records.tsv.

## Raw-record verification

I checked patient TCGA-17-Z023’s TP53 records and confirmed that excluding the Silent mutation gave a final count of 1.

The script also compared all 2830 SQL patient/gene counts with a separate pandas calculation, and all matched. No foreign-key violations were found.

## Gene totals

- TP53: 305 qualifying mutation records.
- KRAS: 172 qualifying mutation records.
- EGFR: 85 qualifying mutation records.
- STK11: 81 qualifying mutation records.
- KEAP1: 103 qualifying mutation records.
