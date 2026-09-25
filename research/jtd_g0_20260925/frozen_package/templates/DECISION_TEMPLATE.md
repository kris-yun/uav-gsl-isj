# JTD-G0 DECISION — 2026-09-25

Branch:  
Base commit:  
Final commit:  
Decision:  

## 1. Input contract

- R0 PASS located:
- Input paths:
- Hashes:
- Sources:
- Independent realizations/source:
- Ordered time×probe structure:
- Duplicate/pseudorep audit:
- Observable:

## 2. Frozen analysis

- Blocks:
- PCs/block:
- CV:
- Covariance:
- Shuffles:
- Prior:

## 3. Primary result

- FULL mean NLL:
- median SHUFFLED mean NLL:
- REL_NLL_GAIN:
- empirical p:
- hierarchical bootstrap 95% CI:

## 4. Stability

| fold | ΔNLL | empirical p | direction |
|---|---:|---:|---|
| F0 | | | |
| F1 | | | |
| F2 | | | |
| F3 | | | |

Positive sources: /18  
LOSO sign positive: /18  

## 5. Secondary ranking

- FULL median truth rank:
- null median truth rank:
- FULL top-1:
- null top-1:
- FULL top-3:
- null top-3:
- MAP error if available:

## 6. Controls

- diagonal covariance:
- block-product:
- null marginal integrity:

## 7. Gate checklist

- [ ] input PASS
- [ ] relative gain >= 5%
- [ ] p <= 0.01
- [ ] bootstrap lower > 0
- [ ] 4/4 fold positive
- [ ] >=12/18 source positive
- [ ] 18/18 LOSO sign positive
- [ ] median truth rank not worse
- [ ] top-3 not >2 pp worse

## 8. Allowed claim

...

## 9. Forbidden claim

...

## 10. Stop statement

No closed loop / no dense-source expansion / no new plume generation / no rescue tuning was run.

## 11. Evidence package

Path:  
SHA256:
