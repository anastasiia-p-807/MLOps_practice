# Lesson 10: ML training automation with AWS Step Functions

Проєкт створює простий MLOps workflow для автоматизації тренування: Step Function послідовно запускає дві Lambda-функції `ValidateData` і `LogMetrics`.

## Структура

```text
mlops-train-automation/
|-- terraform/
|   |-- main.tf
|   |-- data.tf
|   |-- terraform.tf
|   |-- variables.tf
|   |-- outputs.tf
|   `-- lambda/
|       |-- validate.py
|       |-- log_metrics.py
|       |-- validate.zip
|       `-- log_metrics.zip
|-- .gitlab-ci.yml
|-- .github/workflows/train-model.yml
`-- README.md
```

## Передумови

- AWS CLI налаштований з profile `default`.
- Terraform встановлений локально.
- Регіон: `eu-central-1`.

## Створення Lambda archives

PowerShell:

```powershell
cd terraform/lambda
Compress-Archive -Path validate.py -DestinationPath validate.zip -Force
Compress-Archive -Path log_metrics.py -DestinationPath log_metrics.zip -Force
```

## Розгортання Terraform

```powershell
cd terraform
terraform init
terraform plan
terraform apply
```

Після створення подивитися outputs:

```powershell
terraform output
```


## Terraform outputs

```text
state_machine_arn = "arn:aws:states:eu-central-1:616150220350:stateMachine:mlops-train-automation-dev-pipeline"
validate_lambda_name = "mlops-train-automation-dev-validate"
log_metrics_lambda_name = "mlops-train-automation-dev-log-metrics"
```
## Ручний запуск Step Function

Після `terraform apply` взяти `state_machine_arn` з output і виконати:

```powershell
Set-Content -Path input.json -Value '{"source":"manual","dataset":"iris"}' -Encoding ASCII
aws stepfunctions start-execution --region eu-central-1 --state-machine-arn "arn:aws:states:eu-central-1:616150220350:stateMachine:mlops-train-automation-dev-pipeline" --name "train-manual" --input file://input.json --profile default
```

Приклад JSON input:

```json
{
  "source": "manual",
  "dataset": "iris"
}
```

## Перевірка в AWS Console

1. AWS Console -> Step Functions -> State machines.
2. Відкрити `mlops-train-automation-dev-pipeline`.
3. Перейти в Executions.
4. Відкрити execution і перевірити, що кроки `ValidateData` і `LogMetrics` завершилися успішно.
5. AWS Console -> Lambda -> Functions, перевірити створені функції validate і log-metrics.


## Результати виконання

Terraform створив Step Function і дві Lambda-функції:

```text
state_machine_arn = "arn:aws:states:eu-central-1:616150220350:stateMachine:mlops-train-automation-dev-pipeline"
validate_lambda_name = "mlops-train-automation-dev-validate"
log_metrics_lambda_name = "mlops-train-automation-dev-log-metrics"
```

Step Function була запущена вручну:

```text
executionArn = "arn:aws:states:eu-central-1:616150220350:execution:mlops-train-automation-dev-pipeline:train-manual"
status = "SUCCEEDED"
```

Input execution:

```json
{"source":"manual","dataset":"iris"}
```

Output execution містить результат кроку `LogMetrics`:

```json
{
  "status": "metrics_logged",
  "dataset": "iris",
  "metrics": {
    "accuracy": 0.9474,
    "loss": 0.1395
  }
}
```
## GitHub Actions

Фактично робота ведеться в GitHub, тому для автоматичного запуску додано workflow `.github/workflows/train-model.yml`. Він запускає Step Function після push у `main` або `master`, а також вручну через `workflow_dispatch`.

У GitHub потрібно додати secrets:

1. Repository -> Settings.
2. Secrets and variables -> Actions.
3. New repository secret.
4. Додати змінні:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=eu-central-1
AWS_STEP_FUNCTION_ARN=arn:aws:states:eu-central-1:616150220350:stateMachine:mlops-train-automation-dev-pipeline
```

Workflow запускає:

```powershell
aws stepfunctions start-execution
```

І передає JSON такого виду:

```json
{
  "source": "github-actions",
  "commit": "${{ github.sha }}",
  "run_id": "${{ github.run_id }}"
}
```

## GitLab CI

Основний запуск у цьому репозиторії налаштований через GitHub Actions. Файл `.gitlab-ci.yml` також додано як GitLab-варіант, оскільки він вказаний у вимогах завдання.


## Видалення ресурсів

```powershell
cd terraform
terraform destroy
```
