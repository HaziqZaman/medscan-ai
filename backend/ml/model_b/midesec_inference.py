from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn as nn


# =========================
# Model
# =========================
class DoubleConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),

            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class UNet(nn.Module):
    def __init__(self, in_channels: int = 3, out_channels: int = 1):
        super().__init__()

        self.down1 = DoubleConv(in_channels, 64)
        self.pool1 = nn.MaxPool2d(2)

        self.down2 = DoubleConv(64, 128)
        self.pool2 = nn.MaxPool2d(2)

        self.down3 = DoubleConv(128, 256)
        self.pool3 = nn.MaxPool2d(2)

        self.down4 = DoubleConv(256, 512)
        self.pool4 = nn.MaxPool2d(2)

        self.bottleneck = DoubleConv(512, 1024)

        self.up4 = nn.ConvTranspose2d(1024, 512, kernel_size=2, stride=2)
        self.conv4 = DoubleConv(1024, 512)

        self.up3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.conv3 = DoubleConv(512, 256)

        self.up2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.conv2 = DoubleConv(256, 128)

        self.up1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.conv1 = DoubleConv(128, 64)

        self.out_conv = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x):
        d1 = self.down1(x)
        d2 = self.down2(self.pool1(d1))
        d3 = self.down3(self.pool2(d2))
        d4 = self.down4(self.pool3(d3))
        b = self.bottleneck(self.pool4(d4))

        u4 = self.up4(b)
        u4 = torch.cat([u4, d4], dim=1)
        u4 = self.conv4(u4)

        u3 = self.up3(u4)
        u3 = torch.cat([u3, d3], dim=1)
        u3 = self.conv3(u3)

        u2 = self.up2(u3)
        u2 = torch.cat([u2, d2], dim=1)
        u2 = self.conv2(u2)

        u1 = self.up1(u2)
        u1 = torch.cat([u1, d1], dim=1)
        u1 = self.conv1(u1)

        return self.out_conv(u1)


# =========================
# Utilities
# =========================
def encode_image_to_base64(image: np.ndarray) -> str:
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Failed to encode image to PNG.")
    return base64.b64encode(buffer).decode("utf-8")


def mask_to_connected_components(mask_bin: np.ndarray) -> tuple[int, list[dict[str, Any]]]:
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_bin, connectivity=8)

    objects = []
    for idx in range(1, num_labels):  # skip background
        x = int(stats[idx, cv2.CC_STAT_LEFT])
        y = int(stats[idx, cv2.CC_STAT_TOP])
        w = int(stats[idx, cv2.CC_STAT_WIDTH])
        h = int(stats[idx, cv2.CC_STAT_HEIGHT])
        area = int(stats[idx, cv2.CC_STAT_AREA])
        cx = float(centroids[idx][0])
        cy = float(centroids[idx][1])

        objects.append({
            "index": idx,
            "bbox": {"x": x, "y": y, "w": w, "h": h},
            "area": area,
            "centroid": {"x": round(cx, 2), "y": round(cy, 2)},
        })

    return len(objects), objects


def classify_mitotic_activity(count: int) -> str:
    if count <= 1:
        return "low"
    if count <= 3:
        return "moderate"
    return "high"


# =========================
# Predictor
# =========================
class MiDeSeCB2Predictor:
    def __init__(
        self,
        model_path: str | Path,
        image_size: int = 256,
        threshold: float = 0.5,
        min_component_area: int = 20,
        device: str | None = None,
    ):
        self.model_path = Path(model_path)
        self.image_size = image_size
        self.threshold = threshold
        self.min_component_area = min_component_area

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = UNet(in_channels=3, out_channels=1).to(self.device)
        self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        self.model.eval()

    def preprocess(self, image_bgr: np.ndarray):
        original_h, original_w = image_bgr.shape[:2]
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.image_size, self.image_size), interpolation=cv2.INTER_LINEAR)
        normalized = resized.astype(np.float32) / 255.0
        chw = np.transpose(normalized, (2, 0, 1))
        tensor = torch.tensor(chw, dtype=torch.float32).unsqueeze(0).to(self.device)
        return tensor, original_h, original_w

    def postprocess_mask(self, prob_map: np.ndarray, original_w: int, original_h: int):
        pred_bin_small = (prob_map > self.threshold).astype(np.uint8) * 255
        pred_bin = cv2.resize(pred_bin_small, (original_w, original_h), interpolation=cv2.INTER_NEAREST)

        # remove tiny noisy components
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(pred_bin, connectivity=8)
        cleaned = np.zeros_like(pred_bin)

        for idx in range(1, num_labels):
            area = stats[idx, cv2.CC_STAT_AREA]
            if area >= self.min_component_area:
                cleaned[labels == idx] = 255

        return cleaned

    def create_overlay(self, image_bgr: np.ndarray, mask_bin: np.ndarray):
        color_mask = np.zeros_like(image_bgr)
        color_mask[:, :, 2] = mask_bin  # red

        overlay = cv2.addWeighted(image_bgr, 1.0, color_mask, 0.35, 0)

        contours, _ = cv2.findContours(mask_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (0, 255, 255), 2)

        return overlay

    def predict_from_image(self, image_bgr: np.ndarray) -> dict[str, Any]:
        tensor, original_h, original_w = self.preprocess(image_bgr)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.sigmoid(logits).squeeze().cpu().numpy()

        mask_bin = self.postprocess_mask(probs, original_w, original_h)
        overlay = self.create_overlay(image_bgr, mask_bin)

        object_count, objects = mask_to_connected_components(mask_bin)
        activity_level = classify_mitotic_activity(object_count)

        positive_pixels = int(np.count_nonzero(mask_bin))
        coverage_ratio = float(positive_pixels / mask_bin.size)

        findings = {
            "submodel": "midesec_b2",
            "predicted_mitosis_count": object_count,
            "mitotic_activity_level": activity_level,
            "mask_positive_pixels": positive_pixels,
            "coverage_ratio": coverage_ratio,
            "threshold": self.threshold,
            "min_component_area": self.min_component_area,
            "objects": objects,
        }

        return {
            "mask": mask_bin,
            "overlay": overlay,
            "findings": findings,
            "mask_base64": encode_image_to_base64(mask_bin),
            "overlay_base64": encode_image_to_base64(overlay),
        }

    def predict_from_path(self, image_path: str | Path) -> dict[str, Any]:
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            raise ValueError(f"Failed to read image: {image_path}")

        result = self.predict_from_image(image_bgr)
        result["findings"]["source_image"] = str(image_path)
        return result


if __name__ == "__main__":
    MODEL_PATH = "backend/ml/model_b/runs/midesec_b2/best_model.pth"
    IMAGE_PATH = "backend/ml/model_b/data/midesec_prepared/test/images/P00_00.png"

    predictor = MiDeSeCB2Predictor(model_path=MODEL_PATH)
    result = predictor.predict_from_path(IMAGE_PATH)

    print("\n=== B2 Inference Result ===")
    print(json.dumps(result["findings"], indent=2))

    out_dir = Path("backend/storage/analysis/model_b_b2_debug")
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(IMAGE_PATH).stem
    cv2.imwrite(str(out_dir / f"{stem}_pred_mask.png"), result["mask"])
    cv2.imwrite(str(out_dir / f"{stem}_pred_overlay.png"), result["overlay"])

    with (out_dir / f"{stem}_findings.json").open("w", encoding="utf-8") as f:
        json.dump(result["findings"], f, indent=2)

    print(f"[OK] Saved mask to: {out_dir / f'{stem}_pred_mask.png'}")
    print(f"[OK] Saved overlay to: {out_dir / f'{stem}_pred_overlay.png'}")
    print(f"[OK] Saved findings to: {out_dir / f'{stem}_findings.json'}")