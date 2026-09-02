import argparse
from pathlib import Path

import torch
from PIL import Image
from torchvision.models import MobileNet_V2_Weights


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = ROOT_DIR / "model" / "model.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Запускає ImageNet inference з TorchScript-моделлю MobileNetV2.")
    parser.add_argument("image", type=Path, help="Шлях до вхідного зображення.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="Шлях до model/model.pt.")
    parser.add_argument("--top-k", type=int, default=3, help="Кількість predictions для виводу.")
    return parser.parse_args()


def load_image(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Вхідне зображення не знайдено: {path}")
    return Image.open(path).convert("RGB")


def predict(model_path: Path, image_path: Path, top_k: int) -> list[tuple[int, str, float]]:
    if not model_path.exists():
        raise FileNotFoundError(
            f"TorchScript-модель не знайдено: {model_path}. Спочатку запустіть `python export_model.py`."
        )

    weights = MobileNet_V2_Weights.DEFAULT
    transform = weights.transforms()
    categories = weights.meta["categories"]

    image = load_image(image_path)
    batch = transform(image).unsqueeze(0)

    model = torch.jit.load(str(model_path), map_location="cpu")
    model.eval()

    with torch.inference_mode():
        logits = model(batch)
        probabilities = torch.nn.functional.softmax(logits[0], dim=0)
        confidence, class_ids = torch.topk(probabilities, k=top_k)

    predictions = []
    for class_id, score in zip(class_ids.tolist(), confidence.tolist()):
        predictions.append((class_id, categories[class_id], score))
    return predictions


def main() -> None:
    args = parse_args()
    predictions = predict(args.model, args.image, args.top_k)

    print(f"image={args.image}")
    print(f"model={args.model}")
    print("top_predictions:")
    for rank, (class_id, label, confidence) in enumerate(predictions, start=1):
        print(f"{rank}. class_id={class_id} label={label!r} confidence={confidence:.4f}")


if __name__ == "__main__":
    main()
