import json
from datetime import datetime, timezone


def handler(event, context):
    print("Validating data...")
    print(json.dumps(event))

    dataset = event.get("dataset", "iris")
    source = event.get("source", "manual")

    return {
        "status": "validated",
        "dataset": dataset,
        "source": source,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "input": event,
    }
