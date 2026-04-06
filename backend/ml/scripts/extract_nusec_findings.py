from pathlib import Path
import json
import numpy as np
from PIL import Image

from skimage.measure import label, regionprops
from skimage.morphology import remove_small_objects

# =========================
# PATHS
# =========================
PRED_MASK_PATH = Path(r"backend/ml/model_b/results/nusec_pred_mask_00.png")
OUT_JSON_PATH = Path(r"backend/ml/model_b/results/nusec_findings_00.json")

# =========================
# SETTINGS
# =========================
MIN_OBJECT_SIZE = 20   # remove very tiny noise blobs


def main():
    if not PRED_MASK_PATH.exists():
        raise FileNotFoundError(f"Predicted mask not found: {PRED_MASK_PATH.resolve()}")

    mask = Image.open(PRED_MASK_PATH).convert("L")
    mask_arr = np.array(mask)

    # convert to binary
    binary = mask_arr > 127

    # remove tiny noise objects
    cleaned = remove_small_objects(binary, min_size=MIN_OBJECT_SIZE)

    # connected components
    labeled = label(cleaned)
    props = regionprops(labeled)

    image_h, image_w = cleaned.shape
    total_pixels = image_h * image_w

    nuclei_count = len(props)

    if nuclei_count == 0:
        findings = {
            "estimated_nuclei_count": 0,
            "nuclei_density_percent": 0.0,
            "average_nucleus_area_px": 0.0,
            "size_variation_std_px": 0.0,
            "average_irregularity_score": 0.0,
            "interpretation": "No significant nuclei regions were detected in the predicted mask."
        }
    else:
        areas = []
        irregularities = []

        for region in props:
            area = float(region.area)
            perimeter = float(region.perimeter) if region.perimeter > 0 else 0.0

            areas.append(area)

            # circularity = 4*pi*A / P^2
            # irregularity score = 1 - circularity
            if perimeter > 0:
                circularity = (4.0 * np.pi * area) / (perimeter ** 2)
                circularity = max(0.0, min(1.0, circularity))
                irregularity = 1.0 - circularity
            else:
                irregularity = 0.0

            irregularities.append(irregularity)

        nuclei_pixels = float(cleaned.sum())
        nuclei_density_percent = (nuclei_pixels / total_pixels) * 100.0

        avg_area = float(np.mean(areas))
        std_area = float(np.std(areas))
        avg_irregularity = float(np.mean(irregularities))

        # simple text interpretation
        if nuclei_density_percent < 5:
            density_text = "low"
        elif nuclei_density_percent < 15:
            density_text = "moderate"
        else:
            density_text = "high"

        if avg_irregularity < 0.20:
            irregularity_text = "low"
        elif avg_irregularity < 0.40:
            irregularity_text = "moderate"
        else:
            irregularity_text = "high"

        findings = {
            "estimated_nuclei_count": int(nuclei_count),
            "nuclei_density_percent": round(nuclei_density_percent, 2),
            "average_nucleus_area_px": round(avg_area, 2),
            "size_variation_std_px": round(std_area, 2),
            "average_irregularity_score": round(avg_irregularity, 4),
            "density_level": density_text,
            "irregularity_level": irregularity_text,
            "interpretation": (
                f"The predicted nuclei pattern shows {density_text} nuclei density "
                f"with {irregularity_text} shape irregularity."
            )
        }

    OUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    print("NuSeC findings extracted successfully.")
    print(f"Mask used: {PRED_MASK_PATH.resolve()}")
    print(f"Findings saved to: {OUT_JSON_PATH.resolve()}")
    print("\n--- Findings ---")
    for k, v in findings.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()