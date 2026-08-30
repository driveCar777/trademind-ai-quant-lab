# V10 Information Representation Report

Representations tested: REP_RAW, REP_Z60, REP_INTERACT (10 locked products), REP_STATE (5 locked labels).
Lookbacks 20/60/120 are features computed together, not a search axis.
Inferred / LLM / news / live-internet features: forbidden and unused.

SIMPLE_RULE_KILLED features were kept as inputs. That is model-interaction testing, not a reopened OI/DTE/COT/EIA rule.

## Did representation help?
- REP_INTERACT mean val AUC 0.5255 n=12
- REP_RAW mean val AUC 0.5241 n=12
- REP_STATE mean val AUC 0.5242 n=12
- REP_Z60 mean val AUC 0.5265 n=12

Representation failure analysis (future hypotheses only; this mission does not redefine targets):
1. Direction-at-next-open may be the wrong economic target.
2. D1 horizon may be too coarse for the owned microstructure.
3. The series may be non-stationary enough that a shallow frozen model cannot transfer.
4. The owned information set may have no exploitable predictive content after cost.
These are NEW FUTURE HYPOTHESES. This run does not change T1/T2 or rerun.
