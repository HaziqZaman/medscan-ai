from pathlib import Path
from PIL import Image
import numpy as np

from backend.ml.model_b.nusec_inference import predict_nusec_mask_from_pil
from backend.ml.model_b.nusec_features import extract_nusec_findings_from_mask

TEST_IMAGE_PATH = Path(r"backend/ml/processed/nusec/train/images/00.tif.png")

img = Image.open(TEST_IMAGE_PATH)
result = predict_nusec_mask_from_pil(img)

findings = extract_nusec_findings_from_mask(result["mask_array"])

print("Features OK")
for k, v in findings.items():
    print(f"{k}: {v}")