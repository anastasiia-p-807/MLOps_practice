# Lesson 9: MLflow experiments + PushGateway

Проєкт розгортає MLflow, MinIO, PostgreSQL і Prometheus PushGateway через Argo CD, а скрипт `train_and_push.py` запускає кілька ML-експериментів, логуючи метрики в MLflow і PushGateway.

## Структура

```text
mlops-experiments/
|-- argocd/
|   |-- applications/
|   |   |-- mlflow.yaml
|   |   |-- minio.yaml
|   |   |-- postgres.yaml
|   |   `-- pushgateway.yaml
|   `-- manifests/
|       |-- mlflow/
|       |-- minio/
|       `-- postgres/
|-- experiments/
|   |-- train_and_push.py
|   `-- requirements.txt
|-- best_model/
`-- README.md
```

## Передумови

- VPC та EKS з lesson-5 створені.
- Argo CD з lesson-7 встановлений у namespace `infra-tools`.
- `kubectl get nodes` показує Ready node.
- GitOps repository `goit-argo` доступний для Argo CD.
- Для Grafana Explore потрібні Prometheus і Grafana у кластері.

## Розгортання через Argo CD

Файли з `mlops-experiments/argocd` потрібно додати в GitOps repository `goit-argo`, зробити commit і push.

Після цього застосувати Argo CD Applications:

```powershell
kubectl apply -f argocd/applications/minio.yaml
kubectl apply -f argocd/applications/postgres.yaml
kubectl apply -f argocd/applications/mlflow.yaml
kubectl apply -f argocd/applications/pushgateway.yaml
```

Перевірка:

```powershell
kubectl get applications -n infra-tools
kubectl get pods -n mlflow
kubectl get pods -n monitoring
kubectl get svc -n mlflow
kubectl get svc -n monitoring
```

## Port-forward

MLflow UI:

```powershell
kubectl -n mlflow port-forward svc/mlflow 5000:5000
```

PushGateway:

```powershell
kubectl -n monitoring port-forward svc/pushgateway 9091:9091
```

MinIO Console:

```powershell
kubectl -n mlflow port-forward svc/minio 9001:9001
```

## Запуск експериментів

```powershell
cd experiments
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:MLFLOW_TRACKING_URI = "http://localhost:5000"
$env:PUSHGATEWAY_URL = "http://localhost:9091"
.\.venv\Scripts\python.exe train_and_push.py
```

Після успішного запуску найкраща модель буде скопійована в `best_model/`.

## Перевірка метрик

MLflow UI:

```text
http://localhost:5000
```

PushGateway UI:

```text
http://localhost:9091
```

Grafana Explore не використовувалася через зависання AWS IAM Identity Center під час створення користувача, а наявність метрик підтверджено через PushGateway.

```text
mlflow_accuracy
mlflow_loss
```


## Результати виконання

Argo CD Applications:

```text
NAME          SYNC STATUS   HEALTH STATUS
minio         Synced        Healthy
mlflow        OutOfSync     Healthy
postgres      OutOfSync     Healthy
pushgateway   Synced        Healthy
```

Pods у namespace `mlflow`:

```text
NAME                        READY   STATUS    RESTARTS   AGE
minio-8dfb49bf8-zghrz       1/1     Running   0          24m
mlflow-77dbc6b5cc-9wpjn     1/1     Running   0          38m
postgres-54ffc45b66-rwbbc   1/1     Running   0          38m
```

Pods у namespace `monitoring`:

```text
NAME                           READY   STATUS    RESTARTS   AGE
pushgateway-8479b76c4b-qgllg   1/1     Running   0          52m
```

Output `train_and_push.py`:

```text
run_id=764763e702e549948960eef6efa22a94 C=0.1 max_iter=100 accuracy=0.9474 loss=0.3733
run_id=7fe9a9d18e71436496c78fc39a1fc763 C=0.5 max_iter=200 accuracy=0.9474 loss=0.2230
run_id=2b7f7ee69302443ab6aa01075422e3fa C=1.0 max_iter=300 accuracy=0.9474 loss=0.1757
run_id=d8f1a0b736214f96971eea7ed4d9ff59 C=2.0 max_iter=500 accuracy=0.9474 loss=0.1395
best_run_id=d8f1a0b736214f96971eea7ed4d9ff59 accuracy=0.9474 loss=0.1395 model_dir=lesson-9/mlops-experiments/best_model
```

Після успішного запуску найкраща модель збережена в локальній директорії `best_model/`.

## Скриншоти

- MLflow UI з experiment runs
- Метрики `mlflow_accuracy` або `mlflow_loss`
- MinIO bucket `mlflow-artifacts` з model artifacts

## Видалення ресурсів

Спочатку видалити Applications:

```powershell
kubectl delete -f argocd/applications/mlflow.yaml --ignore-not-found
kubectl delete -f argocd/applications/minio.yaml --ignore-not-found
kubectl delete -f argocd/applications/postgres.yaml --ignore-not-found
kubectl delete -f argocd/applications/pushgateway.yaml --ignore-not-found
```

Потім перевірити namespaces:

```powershell
kubectl get ns mlflow
kubectl get ns monitoring
```

EKS/VPC видаляються окремо через Terraform з lesson-5, якщо більше не потрібні.
