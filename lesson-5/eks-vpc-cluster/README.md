# Lesson 5: VPC та EKS через Terraform

Проєкт створює AWS VPC і EKS-кластер через Terraform у двох окремих конфігураціях:
- `vpc/` створює VPC, public/private subnets, NAT Gateway і outputs для EKS.
- `eks/` читає outputs VPC через `terraform_remote_state` і створює EKS-кластер з двома managed node groups.


## Передумови

Потрібно мати встановлені:
- Terraform або OpenTofu;
- AWS CLI;
- kubectl;
- AWS CLI profile або інший безпечний спосіб передати AWS credentials локально.


## Remote state

Перед запуском потрібно створити S3 bucket для Terraform state та заповнити backend-конфіги та terraform.tfvars:
- vpc/backend.hcl
- eks/backend.hcl
- vpc/terraform.tfvars
- eks/terraform.tfvars

Перевірити, що вказано:
- bucket `s3-terraform-bucket-mlops`;
- region `eu-central-1`;
- profile `default`.

В `eks/terraform.tfvars` потрібно вказати той самий `tf_state_bucket`, з якого `eks/` читатиме remote state VPC.


## Запуск VPC
```powershell
cd vpc
terraform init -backend-config=backend.hcl
terraform plan
terraform apply
```
## Запуск EKS
```powershel
cd ../eks
terraform init -backend-config=backend.hcl
terraform plan
terraform apply
```
EKS читає `vpc_id` і `private_subnets` з remote state VPC через `data "terraform_remote_state" "vpc"`.

## Підключення kubectl

Після створення EKS-кластера:
```powershell
aws eks --region eu-central-1 update-kubeconfig --name mlops-lesson-5-dev-eks
kubectl get nodes
```
Очікуваний результат: worker node з `cpu-nodes` має бути у статусі `Ready`. Node group `gpu-nodes` створена як окрема workload-група з `desired_size = 0`, щоб не створювати зайві EC2 instances під час навчального запуску.


## Видалення ресурсів

Потрібно видаляти у зворотному порядку, бо EKS залежить від VPC:
```powershell
cd eks
terraform destroy
cd ../vpc
terraform destroy
```
# Результати виконання

### VPC outputs

```text
azs = tolist([
  "eu-central-1a",
  "eu-central-1b",
])
private_subnets = [
  "subnet-0933da36d660da703",
  "subnet-05a3e17b578d09409",
]
public_subnets = [
  "subnet-033131277fda5367f",
  "subnet-0f28198d3efdacd46",
]
vpc_id = "vpc-0d90f520a1f5160e8"
```

### EKS outputs

```text
cluster_arn = "arn:aws:eks:eu-central-1:616150220350:cluster/mlops-lesson-5-dev-eks"
cluster_endpoint = "https://75F99CD6FD051F818E9566FFB2BB90F8.gr7.eu-central-1.eks.amazonaws.com"
cluster_name = "mlops-lesson-5-dev-eks"
cluster_security_group_id = "sg-0ae30f980e1e7dd0e"
configure_kubectl = "aws eks --region eu-central-1 update-kubeconfig --name mlops-lesson-5-dev-eks"
node_security_group_id = "sg-03bf51f4fb2d6e62c"
```

### Перевірка kubectl

```text
aws eks --region eu-central-1 update-kubeconfig --name mlops-lesson-5-dev-eks --profile default
Added new context arn:aws:eks:eu-central-1:616150220350:cluster/mlops-lesson-5-dev-eks to ***\.kube\config

kubectl get nodes
NAME                                           STATUS   ROLES    AGE   VERSION
ip-10-20-12-81.eu-central-1.compute.internal   Ready    <none>   11m   v1.33.13-eks-cb19647
```

### Висновок

- VPC була створена окремою Terraform-конфігурацією у папці `vpc/`. 
- Конфігурація EKS у папці `eks/` не створювала мережу повторно, а отримала `vpc_id` і `private_subnets` через `terraform_remote_state` з remote state VPC.
- Після створення EKS kubeconfig був оновлений командою `aws eks update-kubeconfig`, а `kubectl get nodes` підтвердив, що worker node має статус `Ready`.
