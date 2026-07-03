# Automation Review Checklist

## Baselines
- Use official implementations when available.
- Verify SurgeCast, Infotaxis, and KLD against official repos or papers.
- Document any simplified benchmark variants clearly.

## Innovations
- Must come from outside robotics/olfaction.
- Cross-domain reasoning must be explicit and traceable.
- Include one-line cross-domain mapping for each innovation.

## Experiments
- Compare MEMP vs DQA_AS and selected baselines.
- Save results in automation/results.
- Provide a short summary with pass/fail decision.

## Deliverables
- Baseline audit report: automation/results/iter1_baseline_audit.md
- MEMP summary: automation/results/iter2_memp_summary.md
- Experiment comparison: automation/results/iter3_comparison.csv
