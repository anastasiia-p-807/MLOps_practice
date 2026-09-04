# Lesson 7: Argo CD через Terraform

Проєкт розгортає Argo CD у вже створеному EKS-кластері через Terraform і Helm. Після встановлення Argo CD окремо застосовується ApplicationSet, який відстежує GitOps-репозиторій зі структурою `namespace/*`.

## Структура

```text
terraform/
`-- argocd/
    |-- main.tf
    |-- variables.tf
    |-- provider.tf
    |-- outputs.tf
    |-- terraform.tf
    |-- backend.tf
    |-- applicationset.yaml
    `-- values/
        `-- argocd-values.yaml
```

## Передумови

- EKS-кластер `mlops-lesson-5-dev-eks` уже створений.
- AWS CLI profile `default` має доступ до EKS.
- `kubectl` підключений до кластера.
- Terraform встановлений локально.
- GitOps-репозиторій `goit-argo` створений і доступний для Argo CD.

## Налаштування Terraform

```powershell
cd terraform\argocd
Copy-Item backend.hcl.example backend.hcl
Copy-Item terraform.tfvars.example terraform.tfvars
```

У `terraform.tfvars` значення `gitops_repo_url` = реальнтй GitOps-репозиторій для Argo CD.

## Запуск Terraform

```powershell
terraform init -backend-config backend.hcl
terraform plan
terraform apply
```

## Перевірка Argo CD

```powershell
kubectl get pods -n infra-tools
kubectl get applications -n infra-tools
```

Має бути кілька pod-ів з префіксом `argocd-`. Після цього потрібно застосувати ApplicationSet:

```powershell
kubectl apply -f applicationset.yaml
kubectl get applications -n infra-tools
```

ApplicationSet має створити Application для директорії `namespace/application`.

P.S. `applicationset.yaml` винесено окремо, щоб створити ApplicationSet вже після встановлення Argo CD CRDs через Helm. Це вирішує помилку `no matches for kind "ApplicationSet"`, яка виникала, коли Helm намагався створити ApplicationSet до реєстрації CRD.

## Вхід в Argo CD UI

Port-forward:

```powershell
kubectl -n infra-tools port-forward svc/argocd-server 8082:80
```

UI відкривається за адресою:

```text
http://localhost:8082
```

## Перевірка GitOps-деплою

```powershell
kubectl get applications -n infra-tools
kubectl get deploy -n application

kubectl get pods -n application
kubectl get svc -n application
```

## Результат запуску

ApplicationSet створив Argo CD Applications, обидві у фінальному стані:

```text
application   Synced   Healthy
infra-tools   Synced   Healthy
```

Demo-застосунок також розгорнувся в namespace `application`:

```text
demo-nginx   2/2   2   2
```

Pods працюють:

```text
demo-nginx-6fb98cd54b-h6tr9   1/1   Running
demo-nginx-6fb98cd54b-rbqpl   1/1   Running
```

Service створений як внутрішній `ClusterIP`:

```text
demo-nginx   ClusterIP   172.20.176.60   <none>   80/TCP
```

Demo відкривається локально через port-forward на порті `8081`:

```powershell
kubectl -n application port-forward deployment/demo-nginx 8081:80
```

Argo CD UI відкривається локально через port-forward на порті `8082`:

```powershell
kubectl -n infra-tools port-forward svc/argocd-server 8082:80
```

Після цього UI доступний за адресою:

```text
http://localhost:8082
```
## GitOps repository:
```text
https://github.com/anastasiia-p-807/goit-argo
```
