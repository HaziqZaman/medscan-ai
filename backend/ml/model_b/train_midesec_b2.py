from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


# =========================
# Reproducibility
# =========================
def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


# =========================
# Dataset
# =========================
class MiDeSeCDataset(Dataset):
    def __init__(self, images_dir: str | Path, masks_dir: str | Path, image_size: int = 256):
        self.images_dir = Path(images_dir)
        self.masks_dir = Path(masks_dir)
        self.image_size = image_size

        self.image_paths = sorted(list(self.images_dir.glob("*.png")))
        if not self.image_paths:
            raise ValueError(f"No images found in {self.images_dir}")

        self.samples: List[Tuple[Path, Path]] = []
        for img_path in self.image_paths:
            stem = img_path.stem
            mask_path = self.masks_dir / f"{stem}_mask.png"
            if mask_path.exists():
                self.samples.append((img_path, mask_path))

        if not self.samples:
            raise ValueError("No image/mask pairs found.")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        img_path, mask_path = self.samples[idx]

        image = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Failed to read image: {img_path}")
        if mask is None:
            raise ValueError(f"Failed to read mask: {mask_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        image = cv2.resize(image, (self.image_size, self.image_size), interpolation=cv2.INTER_LINEAR)
        mask = cv2.resize(mask, (self.image_size, self.image_size), interpolation=cv2.INTER_NEAREST)

        image = image.astype(np.float32) / 255.0
        mask = (mask > 127).astype(np.float32)

        image = np.transpose(image, (2, 0, 1))  # HWC -> CHW
        mask = np.expand_dims(mask, axis=0)      # HW -> 1HW

        return {
            "image": torch.tensor(image, dtype=torch.float32),
            "mask": torch.tensor(mask, dtype=torch.float32),
            "image_path": str(img_path),
            "mask_path": str(mask_path),
        }


# =========================
# Model: Simple U-Net
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
# Loss + Metrics
# =========================
class DiceLoss(nn.Module):
    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)
        probs = probs.view(probs.size(0), -1)
        targets = targets.view(targets.size(0), -1)

        intersection = (probs * targets).sum(dim=1)
        denominator = probs.sum(dim=1) + targets.sum(dim=1)

        dice = (2.0 * intersection + self.smooth) / (denominator + self.smooth)
        return 1.0 - dice.mean()


class BCEDiceLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss()

    def forward(self, logits, targets):
        return self.bce(logits, targets) + self.dice(logits, targets)


def segmentation_metrics(logits, targets, threshold: float = 0.5):
    probs = torch.sigmoid(logits)
    preds = (probs > threshold).float()

    preds = preds.view(preds.size(0), -1)
    targets = targets.view(targets.size(0), -1)

    intersection = (preds * targets).sum(dim=1)
    union = preds.sum(dim=1) + targets.sum(dim=1) - intersection

    dice = (2 * intersection + 1.0) / (preds.sum(dim=1) + targets.sum(dim=1) + 1.0)
    iou = (intersection + 1.0) / (union + 1.0)

    precision = (intersection + 1.0) / (preds.sum(dim=1) + 1.0)
    recall = (intersection + 1.0) / (targets.sum(dim=1) + 1.0)

    return {
        "dice": dice.mean().item(),
        "iou": iou.mean().item(),
        "precision": precision.mean().item(),
        "recall": recall.mean().item(),
    }


# =========================
# Train / Eval
# =========================
@dataclass
class EpochResult:
    loss: float
    dice: float
    iou: float
    precision: float
    recall: float


def run_epoch(model, loader, criterion, optimizer, device, train: bool) -> EpochResult:
    if train:
        model.train()
    else:
        model.eval()

    running_loss = 0.0
    running_dice = 0.0
    running_iou = 0.0
    running_precision = 0.0
    running_recall = 0.0
    num_batches = 0

    for batch in loader:
        images = batch["image"].to(device)
        masks = batch["mask"].to(device)

        if train:
            optimizer.zero_grad()

        with torch.set_grad_enabled(train):
            logits = model(images)
            loss = criterion(logits, masks)

            if train:
                loss.backward()
                optimizer.step()

        metrics = segmentation_metrics(logits, masks)

        running_loss += loss.item()
        running_dice += metrics["dice"]
        running_iou += metrics["iou"]
        running_precision += metrics["precision"]
        running_recall += metrics["recall"]
        num_batches += 1

    if num_batches == 0:
        raise ValueError("No batches processed.")

    return EpochResult(
        loss=running_loss / num_batches,
        dice=running_dice / num_batches,
        iou=running_iou / num_batches,
        precision=running_precision / num_batches,
        recall=running_recall / num_batches,
    )


# =========================
# Save predictions for review
# =========================
def save_preview_predictions(model, dataset, device, out_dir: Path, num_samples: int = 5):
    out_dir.mkdir(parents=True, exist_ok=True)
    model.eval()

    indices = list(range(min(num_samples, len(dataset))))
    with torch.no_grad():
        for i in indices:
            sample = dataset[i]
            image = sample["image"].unsqueeze(0).to(device)
            mask = sample["mask"].squeeze(0).cpu().numpy()

            logits = model(image)
            pred = torch.sigmoid(logits).squeeze().cpu().numpy()
            pred_bin = (pred > 0.5).astype(np.uint8) * 255

            rgb = sample["image"].cpu().numpy().transpose(1, 2, 0)
            rgb = (rgb * 255).astype(np.uint8)
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            gt_mask = (mask.squeeze() * 255).astype(np.uint8)

            pred_overlay = bgr.copy()
            pred_color = np.zeros_like(bgr)
            pred_color[:, :, 2] = pred_bin
            pred_overlay = cv2.addWeighted(pred_overlay, 1.0, pred_color, 0.35, 0)

            gt_overlay = bgr.copy()
            gt_color = np.zeros_like(bgr)
            gt_color[:, :, 1] = gt_mask
            gt_overlay = cv2.addWeighted(gt_overlay, 1.0, gt_color, 0.35, 0)

            cv2.imwrite(str(out_dir / f"sample_{i}_image.png"), bgr)
            cv2.imwrite(str(out_dir / f"sample_{i}_gt_mask.png"), gt_mask)
            cv2.imwrite(str(out_dir / f"sample_{i}_pred_mask.png"), pred_bin)
            cv2.imwrite(str(out_dir / f"sample_{i}_gt_overlay.png"), gt_overlay)
            cv2.imwrite(str(out_dir / f"sample_{i}_pred_overlay.png"), pred_overlay)


# =========================
# Main
# =========================
def main():
    parser = argparse.ArgumentParser(description="Train B2 MiDeSeC mitosis segmentation model")
    parser.add_argument(
        "--data_root",
        default="backend/ml/model_b/data/midesec_prepared",
        help="Prepared MiDeSeC dataset root",
    )
    parser.add_argument("--image_size", type=int, default=256)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument(
        "--output_dir",
        default="backend/ml/model_b/runs/midesec_b2",
        help="Directory to save model and results",
    )
    args = parser.parse_args()

    set_seed(42)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    data_root = Path(args.data_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_dataset = MiDeSeCDataset(
        images_dir=data_root / "train" / "images",
        masks_dir=data_root / "train" / "masks",
        image_size=args.image_size,
    )
    test_dataset = MiDeSeCDataset(
        images_dir=data_root / "test" / "images",
        masks_dir=data_root / "test" / "masks",
        image_size=args.image_size,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    model = UNet(in_channels=3, out_channels=1).to(device)
    criterion = BCEDiceLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_dice = -1.0
    history = []

    for epoch in range(1, args.epochs + 1):
        train_result = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        test_result = run_epoch(model, test_loader, criterion, optimizer, device, train=False)

        epoch_log = {
            "epoch": epoch,
            "train": train_result.__dict__,
            "test": test_result.__dict__,
        }
        history.append(epoch_log)

        print(
            f"Epoch {epoch}/{args.epochs} | "
            f"Train Loss: {train_result.loss:.4f} | Train Dice: {train_result.dice:.4f} | "
            f"Test Loss: {test_result.loss:.4f} | Test Dice: {test_result.dice:.4f} | "
            f"Test IoU: {test_result.iou:.4f}"
        )

        if test_result.dice > best_dice:
            best_dice = test_result.dice
            torch.save(model.state_dict(), output_dir / "best_model.pth")
            print(f"[OK] Saved best model with Test Dice: {best_dice:.4f}")

    torch.save(model.state_dict(), output_dir / "last_model.pth")

    summary = {
        "device": str(device),
        "image_size": args.image_size,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "learning_rate": args.lr,
        "train_samples": len(train_dataset),
        "test_samples": len(test_dataset),
        "best_test_dice": best_dice,
        "history": history,
    }

    with (output_dir / "training_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nGenerating preview predictions from best model...")
    best_model = UNet(in_channels=3, out_channels=1).to(device)
    best_model.load_state_dict(torch.load(output_dir / "best_model.pth", map_location=device))
    save_preview_predictions(
        model=best_model,
        dataset=test_dataset,
        device=device,
        out_dir=output_dir / "preview_predictions",
        num_samples=5,
    )

    print("\n=== Training Complete ===")
    print(f"Best Test Dice: {best_dice:.4f}")
    print(f"Saved to: {output_dir}")


if __name__ == "__main__":
    main()