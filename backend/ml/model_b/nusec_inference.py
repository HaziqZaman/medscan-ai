from io import BytesIO
import base64
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

import torch
from torchvision import transforms

from ml.model_b.nusec_model import UNet

# =========================
# CONFIG
# =========================
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model_b1_nusec_unet_best.pth"
IMAGE_SIZE = 256
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_model = None


def get_nusec_model():
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"NuSeC model not found: {MODEL_PATH.resolve()}")

        model = UNet(in_channels=3, out_channels=1).to(DEVICE)

        try:
            state_dict = torch.load(
                MODEL_PATH,
                map_location=torch.device(DEVICE),
                weights_only=True
            )
        except TypeError:
            state_dict = torch.load(
                MODEL_PATH,
                map_location=torch.device(DEVICE)
            )

        model.load_state_dict(state_dict)
        model.eval()
        _model = model

    return _model


def image_to_base64(img_array: np.ndarray) -> str:
    success, buffer = cv2.imencode(".png", img_array)
    if not success:
        raise ValueError("Failed to encode image")
    return base64.b64encode(buffer).decode("utf-8")


def create_overlay(original_resized: np.ndarray, pred_mask: np.ndarray) -> np.ndarray:
    overlay = original_resized.copy()
    overlay[pred_mask > 0] = [255, 0, 0]

    blended = (0.7 * original_resized + 0.3 * overlay).astype(np.uint8)
    return blended


def extract_nusec_features(pred_mask: np.ndarray) -> dict:
    mask_bin = (pred_mask > 0).astype(np.uint8) * 255

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_bin, connectivity=8)

    areas = []
    irregularities = []

    for idx in range(1, num_labels):  # skip background
        area = int(stats[idx, cv2.CC_STAT_AREA])

        # tiny noise ignore
        if area < 10:
            continue

        component_mask = np.zeros_like(mask_bin)
        component_mask[labels == idx] = 255

        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        cnt = contours[0]
        perimeter = cv2.arcLength(cnt, True)

        areas.append(area)

        if perimeter > 0:
            irregularity = (4 * np.pi * area) / (perimeter * perimeter)
            irregularities.append(float(irregularity))

    nuclei_count = len(areas)
    avg_area = float(np.mean(areas)) if areas else 0.0
    avg_irregularity = float(np.mean(irregularities)) if irregularities else 0.0

    positive_pixels = int(np.count_nonzero(mask_bin))
    coverage_ratio = float(positive_pixels / mask_bin.size)

    if coverage_ratio >= 0.20:
        nuclei_density = "high"
    elif coverage_ratio >= 0.08:
        nuclei_density = "moderate"
    else:
        nuclei_density = "low"

    return {
        "submodel": "nusec_b1",
        "nuclei_count": nuclei_count,
        "avg_nuclei_area": round(avg_area, 2),
        "irregularity_score": round(avg_irregularity, 4),
        "nuclei_density": nuclei_density,
        "mask_positive_pixels": positive_pixels,
        "coverage_ratio": round(coverage_ratio, 4),
    }


def predict_nusec_from_pil(image: Image.Image) -> dict:
    model = get_nusec_model()

    original_rgb = image.convert("RGB")
    resized_pil = original_rgb.resize((IMAGE_SIZE, IMAGE_SIZE))
    resized_np = np.array(resized_pil)

    transform = transforms.Compose([
        transforms.ToTensor(),
    ])

    image_tensor = transform(resized_pil).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(image_tensor)
        probs = torch.sigmoid(logits)
        pred = (probs > 0.5).float()

    prob_map = probs.squeeze().cpu().numpy()
    pred_mask = pred.squeeze().cpu().numpy().astype(np.uint8) * 255

    overlay = create_overlay(resized_np, pred_mask)
    findings = extract_nusec_features(pred_mask)

    return {
        "mask": pred_mask,
        "overlay": overlay,
        "findings": findings,
        "probability_map": prob_map,
        "mask_base64": image_to_base64(pred_mask),
        "overlay_base64": image_to_base64(cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)),
        "device_used": DEVICE,
        "image_size": IMAGE_SIZE
    }


def predict_nusec_from_path(image_path: str | Path) -> dict:
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(image_path)
    result = predict_nusec_from_pil(image)
    result["findings"]["source_image"] = str(image_path)
    return result