# AI Assistance — Lab 4

## Tool used
OpenAI ChatGPT, operating as Codex. The exact underlying model version was not available.

## Assistance received
ChatGPT helped draft SQL queries, Python code and the data dictionary. I modified the SQL and Python code and the README.

## Understanding the code
ChatGPT helped me understand how LEFT JOIN keeps all patients and how the query counts only matching mutation records. 

## Verification
I ran `python build_features.py` on my Mac and reviewed the validation results. The final table retained all 566 patients, and the patient/gene summary contained 2830 rows.

I checked patient TCGA-17-Z023’s original TP53 records: one nonsense mutation and one silent mutation. After excluding the silent mutation, I confirmed that the final TP53 count was 1.


## Limitations
Missing clinical values remain NA. Zero mutation counts mean no qualifying mutation record was found; they do not establish biological absence.