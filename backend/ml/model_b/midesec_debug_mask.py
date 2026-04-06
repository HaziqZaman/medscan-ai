from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np


def read_midesec_polygons(csv_path: str | Path) -> list[np.ndarray]:
    """
    Read MiDeSeC CSV where each row is one mitosis polygon:
    x1,y1,x2,y2,...,xn,yn

    Empty trailing cells are ignored.
    """
    csv_path = Path(csv_path)
    polygons: list[np.ndarray] = []

    with csv_path.open("r", newline="") as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader, start=1):
            values = [v.strip() for v in row if v.strip() != ""]

            if not values:
                continue

            if len(values) % 2 != 0:
                raise ValueError(
                    f"Row {row_idx} in {csv_path.name} has odd number of values. "
                    f"Expected x,y pairs."
                )

            coords = np.array([int(float(v)) for v in values], dtype=np.int32).reshape(-1, 2)

            if len(coords) < 3:
                raise ValueError(
                    f"Row {row_idx} in {csv_path.name} has fewer than 3 points. "
                    f"Not a valid polygon."
                )

            polygons.append(coords)

    return polygons


def create_mask(image_shape: tuple[int, int], polygons: list[np.ndarray]) -> np.ndarray:
    """
    Create binary mask from polygon list.
    image_shape = (height, width)
    """
    h, w = image_shape
    mask = np.zeros((h, w), dtype=np.uint8)

    if polygons:
        cv2.fillPoly(mask, polygons, 255)

    return mask


def create_overlay(image_bgr: np.ndarray, polygons: list[np.ndarray], alpha: float = 0.35) -> np.ndarray:
    """
    Draw polygon fills + outlines on top of image for debugging/visualization.
    """
    overlay = image_bgr.copy()
    color_fill = (0, 0, 255)      # red fill in BGR
    color_outline = (0, 255, 255) # yellow outline in BGR

    if polygons:
        filled = image_bgr.copy()
        cv2.fillPoly(filled, polygons, color_fill)
        overlay = cv2.addWeighted(filled, alpha, overlay, 1 - alpha, 0)

        for poly in polygons:
            cv2.polylines(overlay, [poly], isClosed=True, color=color_outline, thickness=2)

    return overlay


def polygon_area(poly: np.ndarray) -> float:
    return float(cv2.contourArea(poly.astype(np.float32)))


def polygon_centroid(poly: np.ndarray) -> tuple[int, int]:
    m = cv2.moments(poly.astype(np.float32))
    if m["m00"] == 0:
        x, y = poly.mean(axis=0)
        return int(x), int(y)
    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])
    return cx, cy


def extract_findings(polygons: list[np.ndarray], mask: np.ndarray) -> dict:
    areas = [polygon_area(p) for p in polygons]
    centroids = [polygon_centroid(p) for p in polygons]

    findings = {
        "mitosis_count": len(polygons),
        "mask_positive_pixels": int(np.count_nonzero(mask)),
        "coverage_ratio": float(np.count_nonzero(mask) / mask.size),
        "average_polygon_area": float(np.mean(areas)) if areas else 0.0,
        "min_polygon_area": float(np.min(areas)) if areas else 0.0,
        "max_polygon_area": float(np.max(areas)) if areas else 0.0,
        "objects": [
            {
                "index": i + 1,
                "num_points": int(len(poly)),
                "area": float(areas[i]),
                "centroid": {"x": int(centroids[i][0]), "y": int(centroids[i][1])},
            }
            for i, poly in enumerate(polygons)
        ],
    }
    return findings


def save_outputs(
    out_dir: str | Path,
    image_bgr: np.ndarray,
    mask: np.ndarray,
    overlay: np.ndarray,
    findings: dict,
    stem: str,
) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_path = out_dir / f"{stem}_raw.png"
    mask_path = out_dir / f"{stem}_mask.png"
    overlay_path = out_dir / f"{stem}_overlay.png"
    findings_path = out_dir / f"{stem}_findings.json"

    cv2.imwrite(str(image_path), image_bgr)
    cv2.imwrite(str(mask_path), mask)
    cv2.imwrite(str(overlay_path), overlay)

    with findings_path.open("w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    print(f"[OK] Raw saved:      {image_path}")
    print(f"[OK] Mask saved:     {mask_path}")
    print(f"[OK] Overlay saved:  {overlay_path}")
    print(f"[OK] Findings saved: {findings_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug MiDeSeC BMP + CSV polygon mask generation")
    parser.add_argument("--image", required=True, help="Path to raw BMP image")
    parser.add_argument("--csv", required=True, help="Path to matching MiDeSeC CSV file")
    parser.add_argument("--out_dir", default="backend/storage/analysis/model_b_debug", help="Output directory")
    args = parser.parse_args()

    image_path = Path(args.image)
    csv_path = Path(args.csv)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise ValueError(f"Failed to read image: {image_path}")

    h, w = image_bgr.shape[:2]
    polygons = read_midesec_polygons(csv_path)
    mask = create_mask((h, w), polygons)
    overlay = create_overlay(image_bgr, polygons)
    findings = extract_findings(polygons, mask)

    print("\n=== MiDeSeC Findings ===")
    print(f"Image: {image_path.name}")
    print(f"CSV:   {csv_path.name}")
    print(f"Mitosis count: {findings['mitosis_count']}")
    print(f"Mask pixels:   {findings['mask_positive_pixels']}")
    print(f"Coverage:      {findings['coverage_ratio']:.6f}")
    print(f"Avg area:      {findings['average_polygon_area']:.2f}")

    save_outputs(
        out_dir=args.out_dir,
        image_bgr=image_bgr,
        mask=mask,
        overlay=overlay,
        findings=findings,
        stem=image_path.stem,
    )


if __name__ == "__main__":
    main()