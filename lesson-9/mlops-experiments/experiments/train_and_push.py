from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split


os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "minioadmin123")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "iris-logistic-regression")
BEST_MODEL_DIR = Path(__file__).resolve().parents[1] / "best_model"

PARAM_GRID = [
    {"C": 0.1, "max_iter": 100},
    {"C": 0.5, "max_iter": 200},
    {"C": 1.0, "max_iter": 300},
    {"C": 2.0, "max_iter": 500},
]


def push_metrics(run_id: str, accuracy: float, loss: float) -> None:
    registry = CollectorRegistry()
    accuracy_gauge = Gauge(
        "mlflow_accuracy",
        "Accuracy of MLflow experiment run",
        ["run_id"],
        registry=registry,
    )
    loss_gauge = Gauge(
        "mlflow_loss",
        "Log loss of MLflow experiment run",
        ["run_id"],
        registry=registry,
    )
    accuracy_gauge.labels(run_id=run_id).set(accuracy)
    loss_gauge.labels(run_id=run_id).set(loss)
    push_to_gateway(PUSHGATEWAY_URL, job="mlflow_experiment", grouping_key={"run_id": run_id}, registry=registry)


def copy_best_model(source_dir: Path) -> None:
    if BEST_MODEL_DIR.exists():
        shutil.rmtree(BEST_MODEL_DIR)
    shutil.copytree(source_dir, BEST_MODEL_DIR)


def main() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    iris = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        iris.data,
        iris.target,
        test_size=0.25,
        random_state=42,
        stratify=iris.target,
    )

    best = {"accuracy": -1.0, "loss": float("inf"), "run_id": None, "model_dir": None}

    for params in PARAM_GRID:
        with mlflow.start_run() as run:
            model = LogisticRegression(**params, solver="lbfgs")
            model.fit(x_train, y_train)

            predictions = model.predict(x_test)
            probabilities = model.predict_proba(x_test)
            accuracy = accuracy_score(y_test, predictions)
            loss = log_loss(y_test, probabilities)

            mlflow.log_params(params)
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("loss", loss)
            mlflow.sklearn.log_model(model, artifact_path="model")

            run_id = run.info.run_id
            push_metrics(run_id, accuracy, loss)

            with tempfile.TemporaryDirectory() as tmp_dir:
                local_model_dir = Path(tmp_dir) / "model"
                local_model_dir.mkdir(parents=True, exist_ok=True)
                joblib.dump(model, local_model_dir / "model.joblib")

                if accuracy > best["accuracy"] or (
                    accuracy == best["accuracy"] and loss < best["loss"]
                ):
                    best.update(
                        {
                            "accuracy": accuracy,
                            "loss": loss,
                            "run_id": run_id,
                            "model_dir": local_model_dir,
                        }
                    )
                    copy_best_model(local_model_dir)

            print(
                f"run_id={run_id} C={params['C']} max_iter={params['max_iter']} "
                f"accuracy={accuracy:.4f} loss={loss:.4f}"
            )

    print(
        "best_run_id={run_id} accuracy={accuracy:.4f} loss={loss:.4f} model_dir={model_dir}".format(
            run_id=best["run_id"],
            accuracy=best["accuracy"],
            loss=best["loss"],
            model_dir=BEST_MODEL_DIR,
        )
    )


if __name__ == "__main__":
    main()
