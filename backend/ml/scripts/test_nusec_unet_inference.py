from pathlib import Path
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms

# =========================
# PATHS
# =========================
MODEL_PATH = Path(r"backend/ml/model_b/model_b1_nusec_unet_best.pth")
TEST_IMAGE_PATH = Path(r"backend/ml/processed/nusec/train/images/00.tif.png")

OUTPUT_MASK_PATH = Path(r"backend/ml/model_b/results/nusec_pred_mask_00.png")
OUTPUT_OVERLAY_PATH = Path(r"backend/ml/model_b/results/nusec_overlay_00.png")

IMAGE_SIZE = 256
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Current working directory: {Path.cwd()}")
print(f"Using device: {DEVICE}")


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


def load_trained_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH.resolve()}")

    model = UNet(in_channels=3, out_channels=1).to(DEVICE)

    try:
        state_dict = torch.load(
            MODEL_PATH,
            map_location=torch.device(DEVICE),
            weights_only=True
        )
    except TypeError:
        # fallback for older PyTorch versions
        state_dict = torch.load(
            MODEL_PATH,
            map_location=torch.device(DEVICE)
        )

    model.load_state_dict(state_dict)
    model.eval()

    print("Model loaded successfully.")
    print(f"Model path: {MODEL_PATH.resolve()}")

    return model


def main():
    if not TEST_IMAGE_PATH.exists():
        raise FileNotFoundError(f"Image not found: {TEST_IMAGE_PATH.resolve()}")

    model = load_trained_model()

    original = Image.open(TEST_IMAGE_PATH).convert("RGB")
    original_resized = original.resize((IMAGE_SIZE, IMAGE_SIZE))

    transform = transforms.Compose([
        transforms.ToTensor(),
    ])

    image_tensor = transform(original_resized).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(image_tensor)
        probs = torch.sigmoid(logits)
        pred = (probs > 0.5).float()

    pred_mask = pred.squeeze().cpu().numpy().astype(np.uint8) * 255

    OUTPUT_MASK_PATH.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pred_mask).save(OUTPUT_MASK_PATH)

    # simple red overlay
    img_np = np.array(original_resized).copy()
    overlay = img_np.copy()
    overlay[pred_mask > 0] = [255, 0, 0]

    blended = (0.7 * img_np + 0.3 * overlay).astype(np.uint8)
    Image.fromarray(blended).save(OUTPUT_OVERLAY_PATH)

    print("Inference complete.")
    print(f"Image used: {TEST_IMAGE_PATH.resolve()}")
    print(f"Predicted mask saved to: {OUTPUT_MASK_PATH.resolve()}")
    print(f"Overlay saved to       : {OUTPUT_OVERLAY_PATH.resolve()}")
    print(f"Predicted foreground pixels: {(pred_mask > 0).sum()}")


if __name__ == "__main__":
    main()