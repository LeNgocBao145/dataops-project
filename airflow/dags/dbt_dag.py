from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

DBT_CONTAINER = "dbt_airflow_project-dbt-1"
DBT_EXEC = f"docker exec {DBT_CONTAINER}"

dag = DAG(
    "dbt_transform",
    default_args=default_args,
    description="Run dbt models, schema tests, source freshness, and Great Expectations validations",
    schedule_interval=timedelta(minutes=5),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "sqlserver", "testing", "great_expectations"],
)

# ---------------------------------------------------------------------------
# Step 1 — Source freshness check
# ---------------------------------------------------------------------------
dbt_source_freshness = BashOperator(
    task_id="dbt_source_freshness",
    bash_command=f"{DBT_EXEC} dbt source freshness",
    dag=dag,
)

# ---------------------------------------------------------------------------
# Step 2 — dbt run (all models)
# ---------------------------------------------------------------------------
dbt_run = BashOperator(
    task_id="dbt_run",
    bash_command=f"{DBT_EXEC} dbt run",
    dag=dag,
)

# ---------------------------------------------------------------------------
# Step 3a — dbt schema / generic tests (not_null, unique, relationships, etc.)
# ---------------------------------------------------------------------------
dbt_test_schema = BashOperator(
    task_id="dbt_test_schema",
    bash_command=f"{DBT_EXEC} dbt test --select test_type:generic",
    dag=dag,
)

# ---------------------------------------------------------------------------
# Step 3b — dbt singular / custom tests (business-logic assertions)
# ---------------------------------------------------------------------------
dbt_test_singular = BashOperator(
    task_id="dbt_test_singular",
    bash_command=f"{DBT_EXEC} dbt test --select test_type:singular",
    dag=dag,
)

# ---------------------------------------------------------------------------
# Step 4 — Great Expectations data quality validation
# ---------------------------------------------------------------------------
gx_validate = BashOperator(
    task_id="great_expectations_validate",
    bash_command=(f"{DBT_EXEC} python /usr/app/great_expectations/run_gx_suite.py"),
    dag=dag,
    # Run even if one of the dbt tests fails so we still get GX results
    trigger_rule=TriggerRule.ALL_DONE,
)

# ---------------------------------------------------------------------------
# Step 5 — Generate dbt docs (runs regardless of test outcomes on main branch)
# ---------------------------------------------------------------------------
dbt_docs_generate = BashOperator(
    task_id="dbt_docs_generate",
    bash_command=f"{DBT_EXEC} dbt docs generate",
    dag=dag,
    trigger_rule=TriggerRule.ALL_SUCCESS,
)

# ---------------------------------------------------------------------------
# DAG dependency chain
# ---------------------------------------------------------------------------
# source freshness → run models → [schema tests ∥ singular tests] → GX → docs
dbt_source_freshness >> dbt_run >> [dbt_test_schema, dbt_test_singular]
[dbt_test_schema, dbt_test_singular] >> gx_validate >> dbt_docs_generate
