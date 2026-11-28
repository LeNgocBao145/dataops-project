# CI/CD Pipeline & Deployment Automation

This repository uses GitHub Actions for continuous integration, automated deployment across environments, documentation publishing, and deployment monitoring.

## Workflows Overview

| Workflow | Trigger | Purpose |
| :--- | :--- | :--- |
| [dbt-ci.yml](../.github/workflows/dbt-ci.yml) | Push / PR (`main`, `develop`, `feature/**`) | SQL linting (`sqlfluff`), Python linting (`flake8`), `dbt compile`, and `dbt docs generate` |
| [python-quality.yml](../.github/workflows/python-quality.yml) | Push / PR (`**.py`, `airflow/**`) | Python formatting & quality checks (`black`, `flake8`, `pylint`) |
| [pr-checks.yml](../.github/workflows/pr-checks.yml) | Pull Request (`main`, `develop`) | Conventional commit title validation, large file check (>1MB), merge conflict check, PR size check |
| [recce-diff.yml](../.github/workflows/recce-diff.yml) | Pull Request (`main`, `develop`, `dbt/**`) | Runs `dbt test` and Recce data impact/lineage diff with PR comment |
| [deploy.yml](../.github/workflows/deploy.yml) | Push (`develop`, `main`) / `workflow_dispatch` | Automated deployment to `test` & `production`, smoke tests, rollback, Slack notifications, and success-rate tracking |
| [deploy-pages.yml](../.github/workflows/deploy-pages.yml) | Push (`develop`, `main`) / `workflow_dispatch` | Builds and publishes dbt Docs & `dbt-colibri` lineage to GitHub Pages |

## Deployment Process

1. **Pre-deployment validation**: [deploy.sh](../scripts/deploy.sh) runs `dbt deps` and `dbt compile` against the target profile before touching the database.
2. **State backup & logging**: Creates a timestamped backup in `backups/<env>_<timestamp>/` and writes full deployment logs to `logs/deploy_<env>_<timestamp>.log`.
3. **Model execution & testing**: Runs `dbt run` followed by `dbt test` and `dbt docs generate`.
4. **Post-deployment health checks**: Executes [smoke_tests.py](../scripts/smoke_tests.py) to verify table existence, row counts, and non-null primary keys.
5. **Tracking & notifications**: Executes [track_deployment.py](../scripts/track_deployment.py) to update `logs/deployment_history.json`, compute deployment success rates in `$GITHUB_STEP_SUMMARY`, and send Slack notifications (`SLACK_WEBHOOK_URL`).

## Environment Mapping

| Branch | Environment | dbt Target | Database |
| :--- | :--- | :--- | :--- |
| `develop` | `test` | `test` | `AdventureWorks2014_Test` |
| `main` | `production` | `prod` | `AdventureWorks2014_Prod` |
| Local | `dev` | `dev` | `AdventureWorks2014` |

For detailed operational steps, rollback procedures, and deployment monitoring, see the [Deployment Runbook](./DEPLOYMENT_RUNBOOK.md).
