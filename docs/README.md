# Engineering documentation

- [Assessment compliance matrix](submission/compliance-matrix.md)
- [System design, diagrams and API](architecture/README.md)
- [Database DDL](architecture/schema.sql)
- [Security boundaries](security.md)
- [Local operation](local-development.md)
- [Deployment and outstanding account actions](deployment/README.md)
- [Automated validation results](testing/results.md)
- [Live integration verification](testing/live-checks.md)
- [Limitations and future work](limitations.md)
- [Architecture decisions](decisions/README.md)
- [Technical executive brief](submission/technical-executive-brief.md)
- [Engineering implementation report](submission/engineering-design-and-implementation.md)
- [25-minute demonstration walkthrough](submission/walkthrough.md)

Implementation and validation evidence are kept separate from unexecuted account-dependent work. Fixture tests verify contracts and deterministic decisions; they cannot prove live model quality or external tool authorization.

Final PDFs are in `output/pdf/`; source Markdown remains in `docs/submission/`. Generate them with `scripts/build_reports.py` in a Python environment with ReportLab.

## Responsibility, validation and limitations

This module maps implementation claims to reproducible local evidence and separate live acceptance checks. Source modules and scripts supply facts; documentation does not manufacture successful external executions. Run the checks in `testing/results.md`, update their JSON evidence, and cross-check the requirement matrix before submission. PDFs describe the initial implementation; the matrix and current Markdown audit take precedence for present status. Account eligibility, billing state, semantic quality and public deployment remain unavailable to local deterministic tests.
