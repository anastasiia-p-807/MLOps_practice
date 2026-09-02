# Звіт до уроку 3

## Мета

Підготувати відтворюваний runtime для ML inference pretrained-моделі TorchVision MobileNetV2:

- експортувати модель у TorchScript через `torch.jit.trace`;
- використовувати CPU-only PyTorch, бо GPU для цього inference-завдання не потрібен;
- запустити top-3 ImageNet prediction для `example.jpg`;
- порівняти fat Docker-образ і slim multi-stage Docker-образ.

## Команди

```bash
python3 -m pip install -r requirements.txt
python3 export_model.py
python3 app/inference.py example.jpg

docker build -f Dockerfile.fat -t ml-infer-fat:1.0 .
docker build -f Dockerfile.slim -t ml-infer-slim:1.0 .

docker run --rm ml-infer-fat:1.0
docker run --rm ml-infer-slim:1.0

docker images | grep ml-infer
docker history ml-infer-fat:1.0
docker history ml-infer-slim:1.0
```

Якщо використовується Podman, команди еквівалентні:

```bash
podman build -f Dockerfile.fat -t ml-infer-fat:1.0 .
podman build -f Dockerfile.slim -t ml-infer-slim:1.0 .

podman run --rm ml-infer-fat:1.0
podman run --rm ml-infer-slim:1.0

podman images | grep ml-infer
podman history ml-infer-fat:1.0
podman history ml-infer-slim:1.0
```

## Порівняння

Образи були зібрані та перевірені через Podman. `podman images` показав, що fat-образ має розмір 2.07 GB, а slim-образ - 1.06 GB. Отже, slim-варіант приблизно на 1.01 GB менший завдяки базі `python:3.13-slim` і multi-stage підходу.

| Метрика | Fat-образ | Slim-образ |
|---|---:|---:|
| Базовий образ | `python:3.13` | `python:3.13-slim` |
| Тип збірки | одноетапна | багатоетапна |
| Вміст runtime | застосунок, модель, CPU-only залежності, повна базова ОС | застосунок, модель, CPU-only runtime-залежності, slim ОС |
| Розмір образу | 2.07 GB | 1.06 GB |
| Кількість рядків у `podman history` | 22 | 17 |
| Результат inference | top-3 ImageNet predictions | top-3 ImageNet predictions |
| Відтворюваність | висока завдяки pinned packages | висока завдяки pinned packages |

## Результат порівняння образів

Команда:

```powershell
podman images | findstr ml-infer
```

Результат:

```text
localhost/ml-infer-slim  1.0  ee0d496e9f6a  2 minutes ago  1.06 GB
localhost/ml-infer-fat   1.0  befbce3fb2f6  4 minutes ago  2.07 GB
```

Найважливіші рядки з `podman history ml-infer-fat:1.0`:

```text
/bin/sh -c python export_model.py              28.8MB
/bin/sh -c python -m pip install --upgrade...  910MB
FROM docker.io/library/python:3.13
RUN ...                                        668MB
RUN ...                                        190MB
# debian.sh ...                               124MB
```

Найважливіші рядки з `podman history ml-infer-slim:1.0`:

```text
COPY dir:... /install ...                      910MB
COPY dir:... model ...                         14.5MB
FROM docker.io/library/python:3.13-slim
RUN ...                                        37MB
# debian.sh ...                                81.1MB
```

Головна різниця: обидва образи мають великий шар із PyTorch-залежностями приблизно 910 MB, але fat-образ успадковує значно більшу базову систему з `python:3.13`. Slim-образ використовує `python:3.13-slim`, тому його базові OS-шари менші, а фінальний runtime не містить повний набір файлів із builder stage.

## Аналіз

Fat-образ простіше читати й дебажити, тому що він використовує повний Python base image і встановлює залежності прямо в runtime-образ. Компроміс полягає в розмірі: фінальний образ залишає більше OS-пакетів і build-time metadata.

Slim-образ використовує `python:3.13-slim` і окремий builder stage. Залежності встановлюються в `/install`, TorchScript-модель експортується в builder, а runtime stage отримує тільки встановлені Python-пакети, `model/model.pt`, `app/inference.py` і `example.jpg`. Це зменшує runtime surface і зазвичай покращує швидкість передачі образу та зручність deployment.

Поведінка inference має бути однаковою, бо обидва образи запускають ту саму TorchScript-модель і той самий preprocessing з `MobileNet_V2_Weights.DEFAULT.transforms()`. GPU не використовується: модель завантажується з `map_location="cpu"`, а CPU-only PyTorch не тягне CUDA/NVIDIA залежності.

## Результат локального inference

Команда:

```bash
python3 app/inference.py example.jpg
```

Результат top-3 predictions для `example.jpg`:

```text
top_predictions:
1. class_id=285 label='Egyptian cat' confidence=0.1992
2. class_id=284 label='Siamese cat' confidence=0.1991
3. class_id=283 label='Persian cat' confidence=0.1714
```

Модель визначила, що зображення найбільше схоже на класи котів ImageNet. Найвищу confidence отримав клас `Egyptian cat`, але значення близькі між собою, тому модель розглядає кілька схожих варіантів.

## Результат inference у контейнерах

Fat-образ:

```text
podman run --rm ml-infer-fat:1.0
image=example.jpg
model=/app/model/model.pt
top_predictions:
1. class_id=285 label='Egyptian cat' confidence=0.1992
2. class_id=284 label='Siamese cat' confidence=0.1991
3. class_id=283 label='Persian cat' confidence=0.1714
```

Slim-образ:

```text
podman run --rm ml-infer-slim:1.0
image=example.jpg
model=/app/model/model.pt
top_predictions:
1. class_id=285 label='Egyptian cat' confidence=0.1992
2. class_id=284 label='Siamese cat' confidence=0.1991
3. class_id=283 label='Persian cat' confidence=0.1714
```

Результати fat і slim образів збігаються. Це означає, що обидва контейнери використовують одну й ту саму TorchScript-модель, однаковий preprocessing і однакове вхідне зображення.

## Нотатки про локальну перевірку

У початковому системному Python цього workspace були недоступні `torch`, `torchvision` і `Pillow`, тому для локального запуску потрібно використовувати `.venv` на Python 3.13 і встановити залежності з `requirements.txt`. Для контейнерної частини використовувався Podman, який виконує ті самі Dockerfile і створює OCI-сумісні образи. Розмір образів і history виміряні командами `podman images` і `podman history`.

Результати `podman images`, `podman history` і inference у контейнерах внесені в цей звіт.







