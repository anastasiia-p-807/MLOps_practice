from pathlib import Path

import torch
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2


MODEL_PATH = Path(__file__).resolve().parent / "model" / "model.pt"


def main() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    weights = MobileNet_V2_Weights.DEFAULT
    model = mobilenet_v2(weights=weights)
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)
    with torch.inference_mode():
        traced_model = torch.jit.trace(model, dummy_input)

    traced_model.save(str(MODEL_PATH))
    print(f"Saved TorchScript model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
