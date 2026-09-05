import json
from datetime import datetime, timezone


def handler(event, context):
    print("Logging metrics...")
    print(json.dumps(event))

    metrics = {
        "accuracy": 0.9474,
        "loss": 0.1395,
    }

    return {
        "status": "metrics_logged",
        "dataset": event.get("dataset", "iris"),
        "metrics": metrics,
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "previous_step": event,
    }
