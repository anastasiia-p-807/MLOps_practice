TorchScript inference у Docker

Проєкт експортує pretrained-класифікатор MobileNetV2 з `torchvision.models` у TorchScript і запускає top-3 ImageNet inference у двох Docker-образах:

- `Dockerfile.fat` використовує базовий образ `python:3.13`.
- `Dockerfile.slim` використовує multi-stage збірку на `python:3.13-slim` і копіює в runtime тільки потрібні файли.

## Структура

```text
lesson-3/
|-- app/
|   `-- inference.py
|-- model/
|   `-- model.pt
|-- scripts/
|   `-- install_dev_tools.sh
|-- export_model.py
|-- requirements.txt
|-- Dockerfile.fat
|-- Dockerfile.slim
|-- .dockerignore
|-- example.jpg
|-- report.md
`-- README.md
```

Файл `model/model.pt` створюється командою `python3 export_model.py` або автоматично під час Docker-збірки.

## Локальне налаштування

На Linux або WSL:

```bash
chmod +x scripts/install_dev_tools.sh
./scripts/install_dev_tools.sh
```

Скрипт перевіряє Docker, Docker Compose V2, Python, pip і встановлює Python-пакети з `requirements.txt`. Залежності PyTorch встановлюються у CPU-only варіанті, тому CUDA/NVIDIA пакети не потрібні. Вивід записується в `install.log`.

Ручне налаштування Python:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 export_model.py
python3 app/inference.py example.jpg
```

Якщо раніше почала встановлюватися CUDA/NVIDIA версія PyTorch, найчистіший варіант - видалити `.venv`, створити її заново і ще раз виконати встановлення з оновленого `requirements.txt`.

Очікуваний формат результату inference:

```text
image=example.jpg
model=.../model/model.pt
top_predictions:
1. class_id=... label='...' confidence=...
2. class_id=... label='...' confidence=...
3. class_id=... label='...' confidence=...
```

## Збірка Docker-образів

Обидва Dockerfile генерують `model/model.pt` під час збірки образу. `requirements.txt` використовує CPU-only wheels PyTorch, тому образи не повинні завантажувати CUDA-залежності.

```bash
docker build -f Dockerfile.fat -t ml-infer-fat:1.0 .
docker build -f Dockerfile.slim -t ml-infer-slim:1.0 .
```

Якщо замість Docker встановлений Podman, можна виконати еквівалентні команди:

```bash
podman build -f Dockerfile.fat -t ml-infer-fat:1.0 .
podman build -f Dockerfile.slim -t ml-infer-slim:1.0 .
```

## Запуск inference у Docker

Запуск із вбудованим прикладом:

```bash
docker run --rm ml-infer-fat:1.0
docker run --rm ml-infer-slim:1.0
```

Для Podman:

```bash
podman run --rm ml-infer-fat:1.0
podman run --rm ml-infer-slim:1.0
```

Запуск із зображенням, підмонтованим через bind mount:

```bash
docker run --rm -v "$PWD/example.jpg:/app/input.jpg:ro" ml-infer-fat:1.0 input.jpg
docker run --rm -v "$PWD/example.jpg:/app/input.jpg:ro" ml-infer-slim:1.0 input.jpg
```

## Порівняння образів

```bash
docker images | grep ml-infer
docker history ml-infer-fat:1.0
docker history ml-infer-slim:1.0
```

Для Podman:

```bash
podman images | grep ml-infer
podman history ml-infer-fat:1.0
podman history ml-infer-slim:1.0
```

Fat-образ простіший, але більший, тому що залишає повну базу `python:3.13` і build-time шари. Slim-образ менший, бо стартує з `python:3.13-slim`, використовує builder stage і копіює в runtime тільки встановлені пакети, TorchScript-модель, застосунок і приклад зображення.

## Надсилання в GitLab

```bash
git checkout -b lesson-3
git add .
git commit -m "Додати lesson-3: TorchScript-модель, Dockerfile та звіт"
git push --set-upstream origin lesson-3
```

В LMS потрібно надіслати посилання на гілку `lesson-3` і zip-архів із роботою.

## Zip-архів

З кореня репозиторію:

```bash
zip -r lesson-3_homework.zip lesson-3/
unzip -l lesson-3_homework.zip
```


