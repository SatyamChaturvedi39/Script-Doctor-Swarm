# Backend Data Directory

This directory is the plan-spec location for local test data.

## Structure (per implementation plan §5.2)
```
backend/data/
├── test_scripts/         # Screenplay .txt files for testing
├── beat_sheets/          # Beat-sheet answer keys (JSON)
└── canary_injections/    # Canary injection test cases
```

## Note
In the actual implementation, evaluation data lives in `eval/data/` rather
than here, collocated with the evaluation harness scripts. This is a
intentional deviation from the flat plan spec — it keeps eval data next to
eval code, which is cleaner for a solo project.

If you want to test the backend parser in isolation, copy any `.txt`
screenplay from `eval/data/canary_scripts/` into `test_scripts/` here.
