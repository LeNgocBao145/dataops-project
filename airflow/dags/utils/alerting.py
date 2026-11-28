import json
import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class AlertManager:
    """Manage pipeline failure, retry, and data quality alerts via Slack and logs."""

    def __init__(self, webhook_url=None):
        """Initialize AlertManager with an optional Slack webhook URL."""
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")

    def send_slack_alert(self, title, message, severity="info"):
        """Send an alert message to Slack if configured, otherwise log it."""
        color_map = {
            "info": "#36a64f",
            "warning": "#ff9900",
            "error": "#ff0000",
            "critical": "#8b0000",
        }
        payload = {
            "attachments": [
                {
                    "color": color_map.get(severity, "#36a64f"),
                    "title": title,
                    "text": message,
                    "footer": "DataOps Monitoring",
                    "ts": int(datetime.now().timestamp()),
                }
            ]
        }

        logger.info("=== ALERT TRIGGERED [%s] === %s: %s", severity.upper(), title, message)

        if not self.webhook_url:
            logger.info("SLACK_WEBHOOK_URL is not configured; alert logged locally only.")
            return False

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if response.status_code == 200:
                logger.info("Alert successfully sent to Slack.")
                return True
            logger.warning("Slack returned status %s: %s", response.status_code, response.text)
            return False
        except Exception as exc:
            logger.error("Failed to send Slack alert: %s", exc)
            return False

    def alert_pipeline_failure(self, dag_id, task_id, error_message, execution_date=None, log_url=None):
        """Send a critical/error alert when a pipeline task fails."""
        title = f"Pipeline Failure: {dag_id}"
        details = [f"Task `{task_id}` failed."]
        if execution_date:
            details.append(f"Execution Date: {execution_date}")
        details.append(f"Error: {error_message}")
        if log_url:
            details.append(f"Logs: {log_url}")
        return self.send_slack_alert(title, "\n".join(details), "error")

    def alert_task_retry(self, dag_id, task_id, try_number, max_tries, error_message):
        """Send a warning alert when a task is scheduled for retry."""
        title = f"Task Retry: {dag_id}.{task_id}"
        message = (
            f"Task `{task_id}` failed on attempt {try_number}/{max_tries} and will retry.\n" f"Error: {error_message}"
        )
        return self.send_slack_alert(title, message, "warning")

    def alert_pipeline_success(self, dag_id, execution_date=None):
        """Send an informational alert when the pipeline completes successfully."""
        title = f"Pipeline Succeeded: {dag_id}"
        message = f"All tasks in `{dag_id}` completed successfully."
        if execution_date:
            message += f"\nExecution Date: {execution_date}"
        return self.send_slack_alert(title, message, "info")

    def alert_test_failure(self, test_name, failure_count):
        """Send a warning alert for data quality test failures."""
        title = "Data Quality Alert"
        message = f"Test {test_name} failed\n\nFailures: {failure_count}"
        return self.send_slack_alert(title, message, "warning")

    def alert_slow_pipeline(self, dag_id, execution_time, threshold):
        """Send a warning alert when pipeline execution exceeds threshold."""
        title = f"Slow Pipeline: {dag_id}"
        message = f"Execution time: {execution_time:.2f}s (threshold: {threshold}s)"
        return self.send_slack_alert(title, message, "warning")
