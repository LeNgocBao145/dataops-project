# Troubleshooting Guide

This guide covers common issues across Docker, SQL Server, Airflow, dbt, Great Expectations, Monitoring, and CI/CD.

---

## 1. Docker & Volume Issues

### Error: `"Failed to compute cache key"` / `/dbt/: not found` in Airflow

**Symptom:**
```
failed to solve: failed to compute cache key: failed to calculate checksum of ref ...: /dbt/: not found
```

**Common Causes:**
- Missing directory structure (`./dbt`, `./airflow/dags`, `./airflow/logs`, `./airflow/plugins`).
- Stale Docker build cache or volume permission conflicts on Windows.
- CRLF line endings in `.sh` scripts or backslash paths in `docker-compose.yml`.

**Solutions:**
1. **Clean Docker environment:**
   ```bash
   docker-compose down -v
   docker system prune -a
   docker volume prune
   ```
2. **Ensure required directories exist (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Path ./dbt, ./airflow/dags, ./airflow/logs, ./airflow/plugins -Force
   ```
3. **Fix Windows permissions (PowerShell as Administrator):**
   ```powershell
   icacls * /reset
   icacls * /grant Everyone:F /t
   ```
4. **Ensure LF line endings for shell scripts:**
   ```bash
   git config core.autocrlf input
   ```
5. **Rebuild and start services:**
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

## 2. SQL Server & Database Restore Issues

### `AdventureWorks2014` database does not exist or `restore_db.sh` fails

**Symptom:** `dbt debug` or `dbt run` fails with `Cannot open database "AdventureWorks2014" requested by the login`.

**Causes:**
- SQL Server container was still starting up when `restore_db.sh` ran.
- The database was never restored after `docker-compose up`.

**Solutions:**
1. Check if the `sqlserver` container is running and healthy:
   ```bash
   docker-compose ps sqlserver
   docker-compose logs --tail=50 sqlserver
   ```
2. Re-run the restore script once SQL Server is ready:
   ```bash
   docker-compose exec sqlserver /tmp/restore_db.sh
   ```
3. Verify the database exists:
   ```bash
   docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -Q "SELECT name FROM sys.databases"
   ```

### ODBC Driver / SSL Certificate error when connecting from dbt or Python

**Symptom:** `[Microsoft][ODBC Driver 17 for SQL Server]SSL Provider: The certificate chain was issued by an authority that is not trusted` or `host.docker.internal` unreachable.

**Solutions:**
- In [dbt/profiles.yml](./dbt/profiles.yml), ensure `encrypt: False` and `trust_cert: True` are set for `dev`.
- If running `dbt` inside the `dbt` Docker container and `host.docker.internal` fails on Linux, verify `server: sqlserver` (the Docker Compose service name) or add `extra_hosts: ["host.docker.internal:host-gateway"]`.
- Confirm the password meets SQL Server complexity requirements (`SA_PASSWORD=YourStrong@Passw0rd`).

---

## 3. Apache Airflow Issues

### Airflow tasks fail to execute `dbt` commands in the `dbt` container

**Symptom:** `PermissionError: [Errno 13] Permission denied: '/var/run/docker.sock'` or `No such container: dbt_airflow_project-dbt-1`.

**Solutions:**
1. Verify the actual running `dbt` container name:
   ```bash
   docker ps --format "{{.Names}}"
   ```
2. Update `DBT_CONTAINER_NAME` in `airflow/.env` to match the exact container name (default: `dbt_airflow_project-dbt-1`).
3. Ensure `/var/run/docker.sock` is mounted in both `airflow-webserver` and `airflow-scheduler` in [docker-compose.yml](./docker-compose.yml) and that Docker Desktop is running.

### Airflow Web UI (`http://localhost:8085`) is unreachable or `airflow-webserver` restarts

**Solutions:**
1. Check `postgres` health and `airflow-webserver` logs:
   ```bash
   docker-compose logs airflow-webserver
   ```
2. Ensure port `8085` is not occupied by another application.
3. Verify `airflow/.env` exists (copied from [airflow/.env.example](./airflow/.env.example)); `docker-compose.yml` requires it via `env_file`.

---

## 4. dbt Issues

### `Compilation Error: Could not find package 'dbt_utils'` (or `dbt_expectations` / `dbt_date`)

**Solution:** Install dbt packages before running models or tests:
```bash
docker-compose exec dbt dbt deps --profiles-dir .
```

### `dbt source freshness` fails

**Cause:** Source tables in `AdventureWorks2014` have old `ModifiedDate` values or the database was not restored.

**Solution:** Check [dbt/models/sources.yml](./dbt/models/sources.yml) freshness thresholds (`warn_after: 24 hour`, `error_after: 10000 day`) and verify source tables exist in SQL Server.

### `dbt test` fails on singular or schema tests

**Solution:** Inspect failed rows directly using `--store-failures` (already enabled in [dbt/dbt_project.yml](./dbt/dbt_project.yml) under schema `dbt_test_failures`), or run the specific failing test:
```bash
docker-compose exec dbt dbt test --select <model_or_test_name> --profiles-dir .
```

---

## 5. Great Expectations Issues

### `great_expectations_validate` task fails

**Solutions:**
1. Ensure upstream Silver and Gold tables have been materialized by `dbt run` first.
2. Run the validation script manually inside the `dbt` container to inspect detailed output:
   ```bash
   docker-compose exec dbt python /usr/app/great_expectations/run_gx_suite.py
   ```
3. Verify `GX_HOME=/usr/app/great_expectations` is set in the `dbt` service environment.

---

## 6. Monitoring (Prometheus & Grafana) Issues

### No Airflow metrics appearing in Grafana (`http://localhost:3000`)

**Solutions:**
1. Verify `statsd-exporter`, `prometheus`, and `grafana` containers are running:
   ```bash
   docker-compose ps statsd-exporter prometheus grafana
   ```
2. Check Prometheus targets at `http://localhost:9090/targets` to confirm `statsd-exporter:9102` is `UP`.
3. Confirm `AIRFLOW__METRICS__STATSD_ON=True` is set in `airflow-webserver` and `airflow-scheduler`.

---

## 7. Quick Health Check & Complete Reset

Run the built-in health check script from the project root:
```bash
python scripts/health_check.py
```

If the local Docker environment is completely corrupted and needs a clean slate:
```bash
docker-compose down -v
docker system prune -a --volumes
docker-compose up -d --build
docker-compose exec sqlserver /tmp/restore_db.sh
```
