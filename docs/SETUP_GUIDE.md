# Setup Guide

This guide walks through setting up and running the **dbt + Airflow + SQL Server** DataOps pipeline locally using Docker Compose.

---

## 1. Prerequisites

- **Docker Desktop** (Docker Engine & Docker Compose v2+, minimum **4 GB RAM** allocated)
- **Git**
- **Python 3.9+** (optional on host, used for helper scripts such as `scripts/health_check.py`)

> [!TIP]
> On Windows, configure Git to keep LF line endings for shell scripts so Linux containers can execute `.sh` files without errors:
> ```bash
> git config --global core.autocrlf input
> ```

---

## 2. Clone & Configure Environment Variables

1. **Clone the repository:**
   ```bash
   git clone https://github.com/LeNgocBao145/dataops-project.git
   cd dataops-project
   ```

2. **Configure Airflow environment variables:**
   Copy [airflow/.env.example](../airflow/.env.example) to `airflow/.env`:
   ```bash
   cp airflow/.env.example airflow/.env
   ```
   Review and adjust values in `airflow/.env`:

   | Variable | Default | Description |
   | --- | --- | --- |
   | `DBT_CONTAINER_NAME` | `dbt_airflow_project-dbt-1` | Target dbt Docker container name |
   | `DBT_DAG_SCHEDULE` | `@daily` | Airflow schedule interval (`@daily`, `@hourly`, or cron) |
   | `ALERT_EMAIL` | `admin@example.com` | Recipient email for task failure alerts |
   | `SLACK_WEBHOOK_URL` | `""` | Optional Slack incoming webhook URL for alerts |
   | `AIRFLOW__SMTP__*` | `smtp.gmail.com:587` | Optional SMTP settings for `email_on_failure` |

3. **Verify root `.env` (optional for local scripts):**
   Environment templates exist for each stage ([.env.dev](../.env.dev), [.env.test](../.env.test), [.env.prod](../.env.prod)). For local development, `.env` should match `.env.dev` (`DBT_TARGET=dev`, `SQL_SERVER=localhost`, `SQL_USER=sa`, `SQL_PASSWORD=YourStrong@Passw0rd`).

---

## 3. Start Docker Services

Build and start all containers defined in [docker-compose.yml](../docker-compose.yml):

```bash
docker-compose up -d --build
```

This starts the following services:

| Service | Port | Purpose |
| --- | --- | --- |
| `sqlserver` | `1433` | SQL Server 2019 Express (source & warehouse database) |
| `postgres` | `5432` (internal) | Airflow metadata database |
| `airflow-webserver` | `8085` | Airflow Web UI |
| `airflow-scheduler` | — | Airflow DAG scheduler (`LocalExecutor`) |
| `dbt` | `8001` | dbt Core + Great Expectations runner container |
| `statsd-exporter` | `9125/udp`, `9102` | Converts Airflow StatsD metrics for Prometheus |
| `prometheus` | `9090` | Metrics collection & storage |
| `grafana` | `3000` | Pre-provisioned monitoring dashboards |

Wait until all containers are running:
```bash
docker-compose ps
```

---

## 4. Restore the AdventureWorks2014 Database

The `sqlserver` image downloads `AdventureWorks2014.bak` during build ([sqlserver/Dockerfile](../sqlserver/Dockerfile)). Once the `sqlserver` container is up, run the restore script ([sqlserver/restore_db.sh](../sqlserver/restore_db.sh)):

```bash
docker-compose exec sqlserver /tmp/restore_db.sh
```

> [!NOTE]
> `restore_db.sh` waits 20 seconds and restores `AdventureWorks2014` using `sqlcmd`. If SQL Server is still initializing on a first boot, wait a few seconds and re-run the command.

---

## 5. Initialize dbt & Verify Health

1. **Install dbt packages (`dbt_utils`, `dbt_expectations`, `dbt_date`):**
   ```bash
   docker-compose exec dbt dbt deps --profiles-dir .
   ```

2. **Test SQL Server connectivity from dbt:**
   ```bash
   docker-compose exec dbt dbt debug --profiles-dir .
   ```

3. **Run the infrastructure health check (optional, from host):**
   ```bash
   python scripts/health_check.py
   ```

---

## 6. Access Web UIs & Trigger the Pipeline

| Tool | URL | Default Credentials |
| --- | --- | --- |
| **Airflow UI** | http://localhost:8085 | `admin` / `admin` |
| **Grafana** | http://localhost:3000 | `admin` / `admin` |
| **Prometheus** | http://localhost:9090 | — |

Trigger the `dbt_transform` DAG from the Airflow UI or via CLI:
```bash
docker exec dbt_airflow_project-airflow-scheduler-1 airflow dags trigger dbt_transform
```

For common errors during setup, see the [Troubleshooting Guide](../TROUBLESHOOTING.md).
