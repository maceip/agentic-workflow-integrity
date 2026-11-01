# Gate replay (Stage 4 prototype)

Replay over recorded v2 traces. No live Muse hook exists from inside a session; live integration remains an external piece.

| Judge | Precision | Recall | TP | FP | FN | Benign traces false-blocked |
|---|---:|---:|---:|---:|---:|---:|
| oracle_judge | 0.2 | 1.0 | 3 | 12 | 0 | 2 |
| llm_judge | 0.2143 | 1.0 | 3 | 11 | 0 | 1 |

Blocking uses observed previous tokens; a live gate that blocks an event would change later trace evolution in ways replay cannot show.
