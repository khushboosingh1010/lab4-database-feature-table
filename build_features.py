"""Rebuild Lab 4 tables and validation evidence from the supplied SQLite DB."""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd

GENES = ['TP53', 'KRAS', 'EGFR', 'STK11', 'KEAP1']
ROOT = Path(__file__).resolve().parent

# Query 1: one row per patient and target gene, including zero counts.
# The CROSS JOIN creates all 566 x 5 combinations before optional joins.
GENE_SQL = """
WITH target_genes(gene_symbol) AS (
    VALUES ('TP53'), ('KRAS'), ('EGFR'), ('STK11'), ('KEAP1')
)
SELECT p.patient_id, g.gene_symbol, COUNT(m.mutation_id) AS mutation_count
FROM patients AS p
CROSS JOIN target_genes AS g
LEFT JOIN samples AS s ON s.patient_id = p.patient_id
LEFT JOIN mutations AS m ON m.sample_id = s.sample_id
    AND m.gene_symbol = g.gene_symbol
    AND m.variant_classification <> 'Silent'
GROUP BY p.patient_id, g.gene_symbol
ORDER BY p.patient_id, g.gene_symbol
"""

# Query 2: one row per observed site/stage combination; NULL stage is kept.
SITE_SQL = """
SELECT s.tissue_source_site, p.stage,
       COUNT(DISTINCT p.patient_id) AS patient_count
FROM patients AS p
LEFT JOIN samples AS s ON s.patient_id = p.patient_id
GROUP BY s.tissue_source_site, p.stage
ORDER BY s.tissue_source_site, p.stage
"""

BASE_SQL = """
SELECT p.patient_id, p.sex, p.age_at_diagnosis, p.stage,
       s.tissue_source_site, s.tmb_nonsynonymous
FROM patients AS p
LEFT JOIN samples AS s ON s.patient_id = p.patient_id
ORDER BY p.patient_id
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=ROOT / 'data/cohort.db')
    parser.add_argument('--out', type=Path, default=ROOT / 'outputs')
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f'Database not found: {args.db}')
    args.out.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True) as con:
        read = lambda sql: pd.read_sql_query(sql, con)
        scalar = lambda sql: con.execute(sql).fetchone()[0]
        assert scalar('SELECT COUNT(*) FROM patients') == 566
        assert con.execute('PRAGMA foreign_key_check').fetchall() == []
        # Do not silently choose or average samples if a different DB is used.
        multiplicity = read('SELECT patient_id, COUNT(*) AS n FROM samples GROUP BY patient_id')
        assert len(multiplicity) == 566 and multiplicity['n'].eq(1).all()
        assert scalar('SELECT COUNT(*) FROM mutations WHERE variant_classification IS NULL') == 0
        schema = ['# Inspected database schema', '']
        for table in ['patients', 'samples', 'mutations', 'genes']:
            schema += [f'## {table}', '', f'Rows: {scalar("SELECT COUNT(*) FROM " + table)}', '',
                       '```text', str(con.execute(f'PRAGMA table_info({table})').fetchall()),
                       'Foreign keys: ' + str(con.execute(f'PRAGMA foreign_key_list({table})').fetchall()),
                       '```', '']
        (args.out / 'schema_inspection.md').write_text('\n'.join(schema))
        base = read(BASE_SQL)
        counts = read(GENE_SQL)
        sites = read(SITE_SQL)
        raw_join_sql = GENE_SQL.split('GROUP BY')[0].replace(
            'COUNT(m.mutation_id) AS mutation_count', 'm.mutation_id'
        )
        raw_join = read(raw_join_sql)
        assert len(raw_join) == int(counts.mutation_count.clip(lower=1).sum())
        assert raw_join.patient_id.nunique() == 566
        assert len(base) == 566 and base.patient_id.is_unique
        assert len(counts) == 2830 and not counts.duplicated(['patient_id', 'gene_symbol']).any()
        # Independent group enumeration predicts the number of summary rows.
        expected_sites = len(base[['tissue_source_site', 'stage']].drop_duplicates())
        assert len(sites) == expected_sites and sites.patient_count.sum() == 566
        wide = counts.pivot(index='patient_id', columns='gene_symbol', values='mutation_count')
        wide = wide.reindex(columns=GENES).add_suffix('_count').reset_index()
        wide.columns.name = None
        features = base.merge(wide, on='patient_id', how='left', validate='one_to_one')
        assert len(features) == 566 and features.patient_id.is_unique
        assert set(features.patient_id) == set(read('SELECT patient_id FROM patients').patient_id)
        assert features[[g + '_count' for g in GENES]].notna().all().all()
        # Separate raw-record enumeration verifies counts without SQL GROUP BY.
        # Include a patient with multiple calls, a Silent target call, and no calls.
        multi = counts.loc[counts.mutation_count > 1, 'patient_id'].iloc[0]
        silent = scalar("SELECT s.patient_id FROM samples s JOIN mutations m ON m.sample_id=s.sample_id WHERE m.gene_symbol IN ('TP53','KRAS','EGFR','STK11','KEAP1') AND m.variant_classification='Silent' ORDER BY s.patient_id LIMIT 1")
        no_calls = read('SELECT s.patient_id FROM samples s LEFT JOIN mutations m ON m.sample_id=s.sample_id WHERE m.mutation_id IS NULL ORDER BY s.patient_id')
        check_ids = list(dict.fromkeys([multi, silent, no_calls.patient_id.iloc[0]]))
        evidence, checks = [], []
        sample_ids = read('SELECT sample_id, patient_id FROM samples')
        all_raw = read('SELECT * FROM mutations')
        # Independent pandas aggregation checks every patient/gene count.
        target_raw = all_raw.loc[all_raw.gene_symbol.isin(GENES) & all_raw.variant_classification.ne('Silent')]
        independent = target_raw.merge(sample_ids, on='sample_id', validate='many_to_one')
        independent = independent.groupby(['patient_id', 'gene_symbol']).size()
        observed = counts.set_index(['patient_id', 'gene_symbol']).mutation_count
        assert observed.eq(independent.reindex(observed.index, fill_value=0)).all()
        for patient_id in check_ids:
            # Fetch raw calls by sample IDs, independently of the main join.
            selected = sample_ids.loc[sample_ids.patient_id.eq(patient_id), 'sample_id']
            raw = all_raw.loc[all_raw.sample_id.isin(selected) & all_raw.gene_symbol.isin(GENES)]
            evidence.append(raw.assign(patient_id=patient_id))
            for gene in GENES:
                expected = len(raw.loc[raw.gene_symbol.eq(gene) & raw.variant_classification.ne('Silent')])
                actual = int(features.loc[features.patient_id.eq(patient_id), gene + '_count'].iloc[0])
                assert expected == actual
                checks.append([patient_id, gene, expected, actual])
        for frame, filename in [(features, 'feature_table.tsv'), (counts, 'gene_counts_long.tsv'),
                                (sites, 'patients_by_site_stage.tsv'),
                                (pd.concat(evidence, ignore_index=True), 'checked_patient_raw_mutations.tsv'),
                                (pd.DataFrame(checks, columns=['patient_id','gene','raw_record_count','feature_count']), 'patient_checks.tsv'),
                                (no_calls, 'patients_without_mutation_records.tsv')]:
            frame.to_csv(args.out / filename, sep='\t', index=False, na_rep='NA')
        classes = read("SELECT DISTINCT variant_classification FROM mutations WHERE variant_classification <> 'Silent' ORDER BY 1").iloc[:, 0].tolist()
        dictionary = [
            ['patient_id', 'De-identified TCGA patient identifier; unique row key', 'Not applicable', 'patients', 'None observed; required'],
            ['sex', 'Recorded sex', 'Category', 'patients', 'NA; retained without imputation'],
            ['age_at_diagnosis', 'Age at diagnosis', 'Years', 'patients', 'NA; retained without imputation'],
            ['stage', 'Recorded tumor stage; original labels retained', 'Category', 'patients', 'NA; retained without imputation'],
            ['tissue_source_site', 'Recorded tissue source site code', 'Site code', 'samples', 'NA if absent; none observed'],
            ['tmb_nonsynonymous', 'Recorded nonsynonymous tumor mutation burden; not recalculated', 'Mutations per megabase', 'samples', 'NA if absent; none observed'],
        ]
        for gene in GENES:
            dictionary.append([gene + '_count', f'Number of recorded {gene} mutation rows; includes ' + ', '.join(classes) + '; excludes Silent', 'Mutation records', 'mutations via samples.patient_id', '0 = no qualifying record; no NA; does not establish assay completeness'])
        dd = pd.DataFrame(dictionary, columns=['column_name','meaning','units','source_table','missing_value_coding'])
        assert dd.column_name.tolist() == features.columns.tolist()
        dd.to_csv(args.out / 'data_dictionary.tsv', sep='\t', index=False)
        expanded_rows = int(counts.mutation_count.clip(lower=1).sum())
        report = [
            '# Validation results', '',
            '| Check | Expected | Actual |', '|---|---:|---:|',
            f'| Patients before joins | 566 | 566 |',
            f'| After patient/sample LEFT JOIN | 566 | {len(base)} |',
            f'| Query 1 patient/gene groups | 566 × 5 = 2830 | {len(counts)} |',
            f'| Query 2 observed site/stage groups | {expected_sites} | {len(sites)} |',
            f'| Sum of Query 2 patient counts | 566 | {sites.patient_count.sum()} |',
            f'| After merging wide gene counts | 566 | {len(features)} |', '',
            f'Query 1 intermediate grains: patient/target-gene grid = 2830 rows and 566 unique patients; after joining samples = 2830 rows and 566 unique patients (one sample each); after joining qualifying mutation calls = {expanded_rows} rows and 566 unique patients (a call or unmatched placeholder); after grouping = 2830 rows and 566 unique patients. Expanded row count is predicted by summing max(1, qualifying call count) for each patient/gene pair.', '',
            'No expected/actual differences. Query 2 expectation is calculated from distinct site/stage pairs in the base table before running the grouped summary, not sites multiplied by stages: only observed combinations appear.', '',
            'The unaggregated mutation join has one row per matching call (plus unmatched placeholders), so it can expand rows. Query 1 groups back to patient/gene grain before the Python pivot. Patient IDs remain represented through LEFT JOINs.', '',
            '## Missing values', '',
        ]
        for col in base.columns:
            report.append(f'- {col}: {base[col].isna().sum()} missing values retained.')
        report += ['', f'Samples with no mutation records: {len(no_calls)}. Their gene counts are 0 (no qualifying recorded call), not a biological wild-type conclusion. IDs are in patients_without_mutation_records.tsv.', '',
                   '## Raw-record verification', '',
                   'The assistant inspected target-gene raw records and independently counted non-Silent rows for these patients: ' + ', '.join(check_ids) + '.',
                   'All 15 patient/gene comparisons matched. See patient_checks.tsv and checked_patient_raw_mutations.tsv. The student should review these files before submission; this is not a claim of student-performed verification.', '',
                   'All 2830 SQL patient/gene counts also match an independent pandas aggregation of raw mutation records. Foreign-key check: no violations. Exactly one sample per patient observed; the schema does not enforce that restriction. No missing variant classifications observed.', '',
                   '## Gene totals', '']
        report += [f'- {gene}: {int(features[gene + "_count"].sum())} qualifying mutation records.' for gene in GENES]
        (args.out / 'validation_report.md').write_text('\n'.join(report) + '\n')
        print('\n'.join(report))


if __name__ == '__main__':
    main()
