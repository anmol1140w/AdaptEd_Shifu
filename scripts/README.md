# Repository utilities

This area contains repeatable repository-level utilities such as contract
checks, documentation checks and development helpers.

Utilities should be safe to run locally and should not contain credentials or
personal data.

## Synthetic assessment demo

Run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/run_assessment_demo.py
```

The command builds the in-memory runtime, runs synthetic Riya and Arjun
assessment flows through the framework-independent API adapter, follows the
returned adaptive next-item selections, exercises evidence-bound tutor and
quiz support, and prints the teacher intervention queue. The output is
synthetic demo data, not classroom evidence. Assessment-item and quiz answers
are never included in response payloads.
