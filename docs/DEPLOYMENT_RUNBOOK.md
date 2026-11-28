# Deployment Runbook

## 1. Overview & Environments

This runbook describes the standard operating procedures for deploying, monitoring, and rolling back the `dataops_project` dbt + SQL Server pipeline.

| Environment | Git Branch | dbt Target (`dbt/profiles.yml`) | Target Database | Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Development (Local)** | `feature/**` | `dev` | `AdventureWorks2014` | Local Docker / CLI |
| **CI (PR Validation)** | Pull Requests | `ci` / `pr` | `AdventureWorks2014_CI` / `_PR` | Automatic on PR |
| **Test (Staging)** | `develop` | `test` | `AdventureWorks2014_Test` | Merge to `develop` or `workflow_dispatch` |
| **Production** | `main` | `prod` | `AdventureWorks2014_Prod` | Merge to `main` or `workflow_dispatch` |

### Required GitHub Secrets

| Secret | Used By | Purpose |
| :--- | :--- | :--- |
| `SA_PASSWORD` | CI / Deploy / Pages | SQL Server `sa` password for container initialization |
| `TEST_SQL_SERVER`, `TEST_SQL_USER`, `TEST_SQL_PASSWORD` | `deploy-test` | Connection credentials for `test` target |
| `PROD_SQL_SERVER`, `PROD_SQL_USER`, `PROD_SQL_PASSWORD` | `deploy-production`, `deploy-pages` | Connection credentials for `prod` target |
| `SLACK_WEBHOOK_URL` | `deploy-test`, `deploy-production`, `rollback` | Optional Slack Incoming Webhook for deployment alerts |

---

## 2. Deployment Procedures

### 2.1 Automated Deployment (Standard)

1. Open a Pull Request into `develop` (or `main`) following Conventional Commits format (`feat:`, `fix:`, `docs:`, `chore:`, etc.).
2. Verify all CI checks pass:
   - **Pull Request Checks** (`pr-checks.yml`)
   - **DBT CI Pipeline** (`dbt-ci.yml`)
   - **Python Code Quality** (`python-quality.yml`)
   - **Recce PR Data Impact Analysis** (`recce-diff.yml`)
3. Merge the PR. GitHub Actions automatically triggers [deploy.yml](../.github/workflows/deploy.yml):
   - `develop` -> `deploy-test`
   - `main` -> `deploy-production`

### 2.2 Manual Deployment (via GitHub Actions)

1. Go to **Actions** -> **Deploy to Environments** -> **Run workflow**.
2. Select:
   - **Environment**: `test` or `production`
   - **Action**: `deploy`
3. Click **Run workflow** and monitor the job summary.

### 2.3 Manual Deployment (Local / Self-Hosted CLI)

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh <environment> <target>
# Example:
./scripts/deploy.sh test test
```

---

## 3. Pre-Deployment & Post-Deployment Checks

### Pre-Deployment Validation
Executed automatically by [scripts/deploy.sh](../scripts/deploy.sh):
1. `dbt deps --target <target> --profiles-dir .` — installs required packages (`dbt_utils`, `dbt_expectations`, `dbt_date`).
2. `dbt compile --target <target> --profiles-dir .` — validates Jinja, SQL syntax, and model graph before execution.
3. Saves a snapshot of `dbt/target/` into `backups/<env>_<timestamp>/`.

### Post-Deployment Health Checks
1. **dbt Data Quality Tests**: `dbt test --target <target> --profiles-dir .`
2. **Smoke Tests**: [scripts/smoke_tests.py](../scripts/smoke_tests.py) verifies:
   - Critical tables exist (`bronze.brnz_customers`)
   - Minimum row count thresholds are met
   - Primary key columns contain no `NULL` values
3. **Local Infrastructure Health Check** (for Docker Compose environments):
   ```bash
   python scripts/health_check.py
   ```
   Checks running Docker containers, Airflow webserver (`/health`), SQL Server connectivity, dbt compilation, disk usage, and recent `run_results.json`.

---

## 4. Rollback Procedures

### 4.1 Automated Rollback via GitHub Actions (Recommended)

1. Go to **Actions** -> **Deploy to Environments** -> **Run workflow**.
2. Select:
   - **Environment**: `test` or `production`
   - **Action**: `rollback`
   - **rollback_ref**: Enter the target commit SHA, tag, or `HEAD~1` (default).
3. Click **Run workflow**. The `rollback` job checks out `rollback_ref`, re-deploys the previous known-good dbt models, runs `dbt test` + `smoke_tests.py`, logs the rollback in deployment history, and notifies Slack.

### 4.2 Manual Rollback via CLI (`scripts/rollback.sh`)

When rolling back on a host with local `backups/` directories (or after downloading a `*-deployment-<run_id>` artifact from GitHub Actions):

```bash
chmod +x scripts/rollback.sh
# Interactive confirmation:
./scripts/rollback.sh production backups/production_20261128_120000 prod

# Non-interactive (CI/automation):
./scripts/rollback.sh production backups/production_20261128_120000 prod --yes
```

What `rollback.sh` does:
1. Validates the backup directory exists.
2. Restores `dbt/target/` from the selected backup.
3. Re-runs `dbt run --target <target> --profiles-dir .` and `dbt test --target <target> --profiles-dir .`.

---

## 5. Deployment History & Success Rate Monitoring

### 5.1 Automated Tracking (`scripts/track_deployment.py`)
Every run of `deploy.yml` executes [scripts/track_deployment.py](../scripts/track_deployment.py) with `if: always()`:
- **GitHub Step Summary**: Writes a Markdown Deployment Report containing environment, target, status, commit SHA, actor, UTC timestamp, **Deployment Success Rate (%)** across recent completed runs, and a **Recent Deployment History** table.
- **Persistent Artifacts**: Uploads `logs/deploy_<env>_<timestamp>.log`, `logs/deployment_history.json`, `dbt/target/`, and `backups/` as workflow artifacts (`test-deployment-<run_id>` / `production-deployment-<run_id>`).

### 5.2 Checking Deployment Success Rate Locally

```bash
# View local JSON deployment history
cat logs/deployment_history.json

# Query GitHub Actions API for deployment success rate (requires GH_TOKEN)
GITHUB_TOKEN=<token> GITHUB_REPOSITORY=LeNgocBao145/dataops-project \
  python scripts/track_deployment.py --environment production --target prod --status check
```

### 5.3 Monitoring & Alerting Targets
- **Target Deployment Success Rate**: >= 95%
- **Slack Alerts**: Configured via `SLACK_WEBHOOK_URL` secret; triggers on both success (`good`) and failure (`danger`) for `test`, `production`, and `rollback` jobs.
- **Runtime Pipeline Monitoring**: Prometheus + Grafana + StatsD stack in `monitoring/` tracks Airflow DAG/task execution metrics.

---

## 6. Troubleshooting & Escalation

- For Docker volume, permissions, and container issues on Windows/Linux, see [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).
- If a deployment fails:
  1. Inspect the failed step in GitHub Actions or download the `logs/` artifact (`deploy_<env>_<timestamp>.log`).
  2. If `production` is impacted, immediately execute **Section 4.1 (Automated Rollback)** to `HEAD~1` or the last known-good SHA.
  3. Open a `fix:` PR against `develop` and verify `recce-diff.yml` + `dbt-ci.yml` pass before re-deploying.
