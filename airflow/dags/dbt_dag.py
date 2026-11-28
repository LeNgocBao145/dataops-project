"""
Airflow DAG for AdventureWorks dbt + Great Expectations DataOps Pipeline.

Orchestrates the Medallion architecture (Bronze -> Silver -> Gold Core -> Gold Marts)
with layered data quality gates, exponential-backoff retries, structured logging,
and failure notifications (Slack + Email).
"""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

from utils.alerting import AlertManager
from utils.logging_utils import DataOpsLogger, log_task_execution

DBT_CONTAINER = os.getenv("DBT_CONTAINER_NAME", "dbt_airflow_project-dbt-1")
DBT_EXEC = f"docker exec {DBT_CONTAINER}"
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "admin@example.com")
DAG_SCHEDULE = os.getenv("DBT_DAG_SCHEDULE", "@daily")

pipeline_logger = DataOpsLogger("dbt_transform", "airflow_orchestration")
alert_manager = AlertManager()


def on_task_failure_callback(context):
    """Log task failure details and send failure notification via AlertManager."""
    task_instance = context.get("task_instance")
    dag_id = context.get("dag").dag_id if context.get("dag") else "dbt_transform"
    task_id = task_instance.task_id if task_instance else "unknown_task"
    execution_date = context.get("ds", "")
    log_url = task_instance.log_url if task_instance else None
    exception = context.get("exception", "Unknown error")

    log_task_execution(task_id=task_id, status="failed", error=exception)
    pipeline_logger.log_event("TASK_FAILURE", f"{dag_id}.{task_id} failed: {exception}", level="error")
    alert_manager.alert_pipeline_failure(
        dag_id=dag_id,
        task_id=task_id,
        error_message=str(exception),
        execution_date=execution_date,
        log_url=log_url,
    )


def on_task_retry_callback(context):
    """Log task retry details and notify via AlertManager."""
    task_instance = context.get("task_instance")
    dag_id = context.get("dag").dag_id if context.get("dag") else "dbt_transform"
    task_id = task_instance.task_id if task_instance else "unknown_task"
    try_number = task_instance.try_number if task_instance else 1
    max_tries = (task_instance.max_tries + 1) if task_instance else 3
    exception = context.get("exception", "Unknown error")

    log_task_execution(task_id=task_id, status="retrying", error=exception)
    pipeline_logger.log_event(
        "TASK_RETRY",
        f"{dag_id}.{task_id} retrying ({try_number}/{max_tries}): {exception}",
        level="warning",
    )
    alert_manager.alert_task_retry(
        dag_id=dag_id,
        task_id=task_id,
        try_number=try_number,
        max_tries=max_tries,
        error_message=str(exception),
    )


def on_dag_success_callback(context):
    """Log and optionally notify when the entire DAG run succeeds."""
    dag_id = context.get("dag").dag_id if context.get("dag") else "dbt_transform"
    execution_date = context.get("ds", "")
    pipeline_logger.log_event("DAG_SUCCESS", f"{dag_id} completed for {execution_date}", level="info")
    alert_manager.alert_pipeline_success(dag_id=dag_id, execution_date=execution_date)


DAG_DOCS = """
### AdventureWorks dbt & Data Quality Orchestration (`dbt_transform`)

This DAG orchestrates the end-to-end **Medallion Architecture** analytics pipeline on SQL Server:

1. **Preflight Checks (`preflight_checks`)**
   - `dbt_debug`: Verifies dbt profile and SQL Server connectivity.
   - `dbt_source_freshness`: Checks source table freshness against `sources.yml` thresholds.
2. **Bronze Layer (`bronze_layer`)**
   - `dbt_run_bronze` -> `dbt_test_bronze`: Builds raw staging views (`models/bronze`) and validates schema tests.
3. **Silver Layer (`silver_layer`)**
   - `dbt_run_silver` -> `dbt_test_silver`: Cleanses and conforms tables (`models/silver`) and validates schema tests.
4. **Gold Layer (`gold_layer`)**
   - `dbt_run_gold_core` -> `dbt_test_gold_core`: Builds dimensional star schema (`dim_*`, `fct_sales`).
   - `dbt_run_gold_marts` -> `dbt_test_gold_marts`: Builds business marts (`gld_mart_*`).
5. **Data Quality Gates (`data_quality_checks`)**
   - `dbt_test_singular`: Executes custom SQL business-logic assertions (`tests/`).
   - `great_expectations_validate`: Runs Great Expectations suites against Silver & Gold tables.
6. **Documentation (`dbt_docs_generate`)**
   - Generates updated dbt documentation artifacts after all checks pass.

#### Scheduling & Reliability
- **Schedule**: `@daily` (configurable via `DBT_DAG_SCHEDULE`), `catchup=False`, `max_active_runs=1`.
- **Retries**: `2` retries per task with exponential backoff (5 min -> up to 30 min) and 30-min task timeout.
- **Notifications**: Failure & retry callbacks dispatch alerts via `AlertManager` (Slack webhook)
  and Airflow SMTP email.
"""

default_args = {
    "owner": "dataops",
    "depends_on_past": False,
    "email": [ALERT_EMAIL],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "execution_timeout": timedelta(minutes=30),
    "on_failure_callback": on_task_failure_callback,
    "on_retry_callback": on_task_retry_callback,
}

with DAG(
    dag_id="dbt_transform",
    default_args=default_args,
    description="Orchestrate Medallion dbt models, layered tests, Great Expectations, and alerting",
    doc_md=DAG_DOCS,
    schedule_interval=DAG_SCHEDULE,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),
    on_success_callback=on_dag_success_callback,
    tags=["dbt", "sqlserver", "medallion", "data_quality", "great_expectations"],
) as dag:
    # -----------------------------------------------------------------------
    # Stage 1 — Preflight checks (connectivity + source freshness)
    # -----------------------------------------------------------------------
    with TaskGroup(group_id="preflight_checks", tooltip="Verify dbt connectivity and source freshness") as preflight:
        dbt_debug = BashOperator(
            task_id="dbt_debug",
            bash_command=f"{DBT_EXEC} dbt debug",
            doc_md="Verify dbt profile configuration and SQL Server database connectivity.",
        )

        dbt_source_freshness = BashOperator(
            task_id="dbt_source_freshness",
            bash_command=f"{DBT_EXEC} dbt source freshness",
            doc_md="Check source table freshness against `models/sources.yml` SLA thresholds.",
        )

        dbt_debug >> dbt_source_freshness

    # -----------------------------------------------------------------------
    # Stage 2 — Bronze layer (raw views + schema tests)
    # -----------------------------------------------------------------------
    with TaskGroup(group_id="bronze_layer", tooltip="Build and test Bronze staging models") as bronze_layer:
        dbt_run_bronze = BashOperator(
            task_id="dbt_run_bronze",
            bash_command=f"{DBT_EXEC} dbt run --select path:models/bronze",
        )

        dbt_test_bronze = BashOperator(
            task_id="dbt_test_bronze",
            bash_command=f"{DBT_EXEC} dbt test --select path:models/bronze",
        )

        dbt_run_bronze >> dbt_test_bronze

    # -----------------------------------------------------------------------
    # Stage 3 — Silver layer (cleansed tables + schema tests)
    # -----------------------------------------------------------------------
    with TaskGroup(group_id="silver_layer", tooltip="Build and test Silver conformed models") as silver_layer:
        dbt_run_silver = BashOperator(
            task_id="dbt_run_silver",
            bash_command=f"{DBT_EXEC} dbt run --select path:models/silver",
        )

        dbt_test_silver = BashOperator(
            task_id="dbt_test_silver",
            bash_command=f"{DBT_EXEC} dbt test --select path:models/silver",
        )

        dbt_run_silver >> dbt_test_silver

    # -----------------------------------------------------------------------
    # Stage 4 — Gold layer (core star schema -> business marts)
    # -----------------------------------------------------------------------
    with TaskGroup(group_id="gold_layer", tooltip="Build and test Gold core and mart models") as gold_layer:
        dbt_run_gold_core = BashOperator(
            task_id="dbt_run_gold_core",
            bash_command=f"{DBT_EXEC} dbt run --select path:models/gold/core",
        )

        dbt_test_gold_core = BashOperator(
            task_id="dbt_test_gold_core",
            bash_command=f"{DBT_EXEC} dbt test --select path:models/gold/core",
        )

        dbt_run_gold_marts = BashOperator(
            task_id="dbt_run_gold_marts",
            bash_command=f"{DBT_EXEC} dbt run --select path:models/gold/marts",
        )

        dbt_test_gold_marts = BashOperator(
            task_id="dbt_test_gold_marts",
            bash_command=f"{DBT_EXEC} dbt test --select path:models/gold/marts",
        )

        dbt_run_gold_core >> dbt_test_gold_core >> dbt_run_gold_marts >> dbt_test_gold_marts

    # -----------------------------------------------------------------------
    # Stage 5 — Cross-layer Data Quality Gates (singular tests + Great Expectations)
    # -----------------------------------------------------------------------
    with TaskGroup(
        group_id="data_quality_checks", tooltip="Run singular dbt tests and Great Expectations"
    ) as dq_checks:
        dbt_test_singular = BashOperator(
            task_id="dbt_test_singular",
            bash_command=f"{DBT_EXEC} dbt test --select test_type:singular",
            doc_md="Run custom SQL business-logic assertions in `dbt/tests/`.",
        )

        gx_validate = BashOperator(
            task_id="great_expectations_validate",
            bash_command=f"{DBT_EXEC} python /usr/app/great_expectations/run_gx_suite.py",
            doc_md="Run Great Expectations validation suites across Silver and Gold tables.",
        )

    # -----------------------------------------------------------------------
    # Stage 6 — Generate dbt documentation
    # -----------------------------------------------------------------------
    dbt_docs_generate = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"{DBT_EXEC} dbt docs generate",
        trigger_rule=TriggerRule.ALL_SUCCESS,
        doc_md="Generate dbt catalog and manifest artifacts for documentation.",
    )

    # -----------------------------------------------------------------------
    # End-to-end DAG dependency chain
    # -----------------------------------------------------------------------
    preflight >> bronze_layer >> silver_layer >> gold_layer >> dq_checks >> dbt_docs_generate
