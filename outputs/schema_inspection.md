# Inspected database schema

## patients

Rows: 566

```text
[(0, 'patient_id', 'TEXT', 0, None, 1), (1, 'sex', 'TEXT', 0, None, 0), (2, 'age_at_diagnosis', 'REAL', 0, None, 0), (3, 'stage', 'TEXT', 0, None, 0), (4, 'vital_status', 'TEXT', 0, None, 0), (5, 'followup_months', 'REAL', 0, None, 0)]
Foreign keys: []
```

## samples

Rows: 566

```text
[(0, 'sample_id', 'TEXT', 0, None, 1), (1, 'patient_id', 'TEXT', 1, None, 0), (2, 'tissue_source_site', 'TEXT', 0, None, 0), (3, 'tmb_nonsynonymous', 'REAL', 0, None, 0), (4, 'aneuploidy_score', 'REAL', 0, None, 0), (5, 'msi_mantis_score', 'REAL', 0, None, 0)]
Foreign keys: [(0, 0, 'patients', 'patient_id', 'patient_id', 'NO ACTION', 'NO ACTION', 'NONE')]
```

## mutations

Rows: 200789

```text
[(0, 'mutation_id', 'INTEGER', 0, None, 1), (1, 'sample_id', 'TEXT', 1, None, 0), (2, 'gene_symbol', 'TEXT', 1, None, 0), (3, 'variant_classification', 'TEXT', 0, None, 0), (4, 'variant_type', 'TEXT', 0, None, 0), (5, 'protein_change', 'TEXT', 0, None, 0), (6, 'chromosome', 'TEXT', 0, None, 0), (7, 'start_pos', 'INTEGER', 0, None, 0), (8, 'end_pos', 'INTEGER', 0, None, 0), (9, 't_ref_count', 'INTEGER', 0, None, 0), (10, 't_alt_count', 'INTEGER', 0, None, 0)]
Foreign keys: [(0, 0, 'genes', 'gene_symbol', 'gene_symbol', 'NO ACTION', 'NO ACTION', 'NONE'), (1, 0, 'samples', 'sample_id', 'sample_id', 'NO ACTION', 'NO ACTION', 'NONE')]
```

## genes

Rows: 17756

```text
[(0, 'gene_symbol', 'TEXT', 0, None, 1), (1, 'entrez_gene_id', 'INTEGER', 0, None, 0), (2, 'chromosome', 'TEXT', 0, None, 0)]
Foreign keys: []
```
