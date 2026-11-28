#!/usr/bin/env python3
"""
Track deployment history and monitor deployment success rates.
Queries GitHub Actions workflow runs when GITHUB_TOKEN & GITHUB_REPOSITORY are set,
and maintains a local JSON history in logs/deployment_history.json.
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error


def record_local_deployment(history_file: Path, entry: dict) -> list:
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []
    history.insert(0, entry)
    history = history[:50]
    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return history


def fetch_github_workflow_runs(repo: str, workflow_file: str, token: str, limit: int = 30) -> list:
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/runs?per_page={limit}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "dataops-deployment-tracker",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("workflow_runs", [])
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"⚠️ Could not fetch GitHub workflow runs: {exc}")
        return []


def compute_metrics(runs: list) -> dict:
    completed = [r for r in runs if r.get("status") == "completed"]
    total = len(completed)
    succeeded = sum(1 for r in completed if r.get("conclusion") == "success")
    failed = sum(1 for r in completed if r.get("conclusion") == "failure")
    cancelled = sum(1 for r in completed if r.get("conclusion") == "cancelled")
    rate = (succeeded / total * 100.0) if total > 0 else 0.0
    return {
        "total_completed": total,
        "succeeded": succeeded,
        "failed": failed,
        "cancelled": cancelled,
        "success_rate_pct": round(rate, 2),
    }


def render_summary(entry: dict, metrics: dict, recent_runs: list) -> str:
    lines = [
        "## 🚀 Deployment Report",
        "",
        "| Field | Value |",
        "| :--- | :--- |",
        f"| **Environment** | `{entry['environment']}` |",
        f"| **Target** | `{entry['target']}` |",
        f"| **Status** | `{entry['status']}` |",
        f"| **Commit** | `{entry['commit'][:7]}` |",
        f"| **Actor** | `{entry['actor']}` |",
        f"| **Timestamp (UTC)** | `{entry['timestamp']}` |",
        "",
        "### 📊 Deployment Success Rate (Recent Workflow Runs)",
        "",
        f"- **Total Completed Runs:** {metrics['total_completed']}",
        f"- **Succeeded:** {metrics['succeeded']}",
        f"- **Failed:** {metrics['failed']}",
        f"- **Success Rate:** **{metrics['success_rate_pct']}%**",
        "",
    ]
    if recent_runs:
        lines.extend(
            [
                "### 📜 Recent Deployment History",
                "",
                "| Run # | Branch | Event | Conclusion | Created At |",
                "| :--- | :--- | :--- | :--- | :--- |",
            ]
        )
        for run in recent_runs[:10]:
            num = run.get("run_number", "-")
            branch = run.get("head_branch", "-")
            event = run.get("event", "-")
            conclusion = run.get("conclusion") or run.get("status", "-")
            created = run.get("created_at", "-")
            lines.append(f"| #{num} | `{branch}` | `{event}` | `{conclusion}` | `{created}` |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Track deployment history and success rates")
    parser.add_argument("--environment", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--workflow", default="deploy.yml")
    parser.add_argument("--history-file", default="logs/deployment_history.json")
    args = parser.parse_args()

    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "environment": args.environment,
        "target": args.target,
        "status": args.status,
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "actor": os.environ.get("GITHUB_ACTOR", os.environ.get("USERNAME", "local")),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    }

    history = record_local_deployment(Path(args.history_file), entry)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    gh_runs = fetch_github_workflow_runs(repo, args.workflow, token) if (repo and token) else []

    if gh_runs:
        metrics = compute_metrics(gh_runs)
    else:
        local_runs = [
            {"status": "completed", "conclusion": "success" if h["status"] == "success" else "failure"} for h in history
        ]
        metrics = compute_metrics(local_runs)

    summary_md = render_summary(entry, metrics, gh_runs)
    print(summary_md)

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write(summary_md + "\n")


if __name__ == "__main__":
    main()
