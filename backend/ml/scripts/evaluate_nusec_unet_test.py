import csv
from pathlib import Path

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

# =========================
# CONFIG
# =========================
MODEL_PATH = Path(r"backend/ml/model_b/model_b1_nusec_unet_best.pth")

TEST_IMG_DIR = Path(r"backend/ml/processed/nusec/test/images")
TEST_MASK_DIR = Path(r"backend/ml/processed/nusec/test/masks_binary")

RESULTS_DIR = Path(r"backend/ml/model_b/test_results")

IMAGE_SIZE = 256
BATCH_SIZE = 4
NUM_WORKERS = 0
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Using device: {DEVICE}")


# =========================
# DATASET
# =========================
class NuSegTestDataset(Dataset):
    def __init__(self, img_dir, mask_dir):
        self.items = []

        img_files = sorted(img_dir.glob("*.png"))
        mask_files = sorted(mask_dir.glob("*.png"))

        img_map = {f.name: f for f in img_files}
        mask_map = {f.name: f for f in mask_files}

        matched = sorted(set(img_map.keys()) & set(mask_map.keys()))

        for name in matched:
            self.items.append({
                "name": name,
                "image_path": img_map[name],
                "mask_path": mask_map[name]
            })

        self.img_transform = transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
        ])

        self.mask_resize = transforms.Resize((IMAGE_SIZE, IMAGE_SIZE))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]

        image = Image.open(item["image_path"]).convert("RGB")
        mask = Image.open(item["mask_path"]).convert("L")

        image_tensor = self.img_transform(image)

        mask = self.mask_resize(mask)
        mask = np.array(mask, dtype=np.float32)
        mask = (mask > 127).astype(np.float32)
        mask_tensor = torch.from_numpy(mask).unsqueeze(0)

        return image_tensor, mask_tensor, item["name"], str(item["image_path"])


# =========================
# MODEL
# =========================
class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),

            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class UNet(nn.Module):
    def __init__(self, in_channels=3, out_channels=1):
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

        self.up4 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        self.conv4 = DoubleConv(1024, 512)

        self.up3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.conv3 = DoubleConv(512, 256)

        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.conv2 = DoubleConv(256, 128)

        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.conv1 = DoubleConv(128, 64)

        self.final = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x):
        d1 = self.down1(x)
        p1 = self.pool1(d1)

        d2 = self.down2(p1)
        p2 = self.pool2(d2)

        d3 = self.down3(p2)
        p3 = self.pool3(d3)

        d4 = self.down4(p3)
        p4 = self.pool4(d4)

        bn = self.bottleneck(p4)

        u4 = self.up4(bn)
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

        return self.final(u1)


# =========================
# LOSS / METRIC
# =========================
bce_loss = nn.BCEWithLogitsLoss()

def dice_score_from_logits(logits, targets, threshold=0.5, eps=1e-6):
    probs = torch.sigmoid(logits)
    preds = (probs > threshold).float()

    intersection = (preds * targets).sum(dim=(1, 2, 3))
    union = preds.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))

    dice = (2.0 * intersection + eps) / (union + eps)
    return dice.mean().item()


def save_overlay(original_path, pred_mask_np, save_path):
    original = Image.open(original_path).convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
    img_np = np.array(original).copy()

    overlay = img_np.copy()
    overlay[pred_mask_np > 0] = [255, 0, 0]

    blended = (0.7 * img_np + 0.3 * overlay).astype(np.uint8)
    Image.fromarray(blended).save(save_path)


@torch.no_grad()
def evaluate(model, loader):
    model.eval()
    total_loss = 0.0
    total_dice = 0.0

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    saved_examples = 0

    for images, masks, names, image_paths in loader:
        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        logits = model(images)
        loss = bce_loss(logits, masks)
        dice = dice_score_from_logits(logits, masks)

        total_loss += loss.item()
        total_dice += dice

        probs = torch.sigmoid(logits)
        preds = (probs > 0.5).float().cpu().numpy()

        for i in range(len(names)):
            if saved_examples < 3:
                pred_mask = preds[i, 0].astype(np.uint8) * 255

                mask_save_path = RESULTS_DIR / f"pred_{names[i]}"
                overlay_save_path = RESULTS_DIR / f"overlay_{names[i]}"

                Image.fromarray(pred_mask).save(mask_save_path)
                save_overlay(image_paths[i], pred_mask, overlay_save_path)

                saved_examples += 1

    avg_loss = total_loss / len(loader)
    avg_dice = total_dice / len(loader)

    return avg_loss, avg_dice


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH.resolve()}")

    dataset = NuSegTestDataset(TEST_IMG_DIR, TEST_MASK_DIR)
    print(f"Test samples: {len(dataset)}")

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS
    )

    model = UNet(in_channels=3, out_channels=1).to(DEVICE)

    try:
        state_dict = torch.load(MODEL_PATH, map_location=torch.device(DEVICE), weights_only=True)
    except TypeError:
        state_dict = torch.load(MODEL_PATH, map_location=torch.device(DEVICE))

    model.load_state_dict(state_dict)
    model.eval()

    test_loss, test_dice = evaluate(model, loader)

    print("\n=== Test Results ===")
    print(f"Test Loss: {test_loss:.4f}")
    print(f"Test Dice: {test_dice:.4f}")
    print(f"Sample predictions saved in: {RESULTS_DIR.resolve()}")


if __name__ == "__main__":
    main()