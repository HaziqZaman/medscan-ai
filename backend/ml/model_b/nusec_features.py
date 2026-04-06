import numpy as np
from skimage.measure import label, regionprops
from skimage.morphology import remove_small_objects

MIN_OBJECT_SIZE = 20


def extract_nusec_findings_from_mask(mask_array: np.ndarray) -> dict:
    """
    mask_array expected:
    - 2D numpy array
    - binary mask values like 0 and 255 (or 0 and 1)
    """

    if mask_array.ndim != 2:
        raise ValueError("mask_array must be a 2D array")

    binary = mask_array > 0
    cleaned = remove_small_objects(binary, min_size=MIN_OBJECT_SIZE)

    labeled = label(cleaned)
    props = regionprops(labeled)

    image_h, image_w = cleaned.shape
    total_pixels = image_h * image_w

    nuclei_count = len(props)

    if nuclei_count == 0:
        return {
            "estimated_nuclei_count": 0,
            "nuclei_density_percent": 0.0,
            "average_nucleus_area_px": 0.0,
            "size_variation_std_px": 0.0,
            "average_irregularity_score": 0.0,
            "density_level": "low",
            "irregularity_level": "low",
            "interpretation": "No significant nuclei regions were detected in the predicted mask."
        }

    areas = []
    irregularities = []

    for region in props:
        area = float(region.area)
        perimeter = float(region.perimeter) if region.perimeter > 0 else 0.0

        areas.append(area)

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

    return {
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