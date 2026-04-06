from pathlib import Path
from PIL import Image

from backend.ml.model_b.nusec_inference import predict_nusec_mask_from_pil

TEST_IMAGE_PATH = Path(r"backend/ml/processed/nusec/train/images/00.tif.png")

img = Image.open(TEST_IMAGE_PATH)
result = predict_nusec_mask_from_pil(img)

print("Inference OK")
print("Mask shape:", result["mask_array"].shape)
print("Device:", result["device_used"])
print("Mask base64 length:", len(result["mask_base64"]))
print("Overlay base64 length:", len(result["overlay_base64"]))