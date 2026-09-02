## Ручне налаштування Python

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe export_model.py
.\.venv\Scripts\python.exe app\inference.py example.jpg
```

## Збірка образів у Podman

Обидва Dockerfile генерують `model/model.pt` під час збірки образу.

```powershell
podman build -f Dockerfile.fat -t ml-infer-fat:1.0 .
podman build -f Dockerfile.slim -t ml-infer-slim:1.0 .
```

## Запуск inference у Podman

Запуск із зображенням `example.jpg`, яке було скопійоване в образ під час збірки:

```powershell
podman run --rm ml-infer-fat:1.0
podman run --rm ml-infer-slim:1.0
```

Запуск із зовнішнім зображенням через bind mount, якщо потрібно перевірити інший файл без повторної збірки образу:

```powershell
podman run --rm -v "${PWD}/example.jpg:/app/input.jpg:ro" ml-infer-fat:1.0 input.jpg
podman run --rm -v "${PWD}/example.jpg:/app/input.jpg:ro" ml-infer-slim:1.0 input.jpg
```

## Порівняння образів

```powershell
podman images | findstr ml-infer
podman history ml-infer-fat:1.0
podman history ml-infer-slim:1.0
```

У виконаній перевірці fat-образ мав розмір `2.07 GB`, а slim-образ - `1.06 GB`. Slim-образ менший, тому що використовує `python:3.13-slim` і multi-stage підхід: у runtime потрапляють застосунок, TorchScript-модель, приклад зображення та встановлені runtime-залежності, але не повна базова система fat-образу.

## Результат

Локальний запуск і запуск у двох Podman-образах дали однакові top-3 predictions для `example.jpg`:

```text
1. class_id=285 label='Egyptian cat' confidence=0.1992
2. class_id=284 label='Siamese cat' confidence=0.1991
3. class_id=283 label='Persian cat' confidence=0.1714
```

Це означає, що локальний Python runtime, fat-образ і slim-образ використовують одну й ту саму TorchScript-модель, однаковий preprocessing з `MobileNet_V2_Weights.DEFAULT.transforms()` і однакове вхідне зображення.

