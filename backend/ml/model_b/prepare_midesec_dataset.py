from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np


VALID_IMAGE_EXTS = {".bmp", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def read_midesec_polygons(csv_path: Path) -> list[np.ndarray]:
    polygons: list[np.ndarray] = []

    with csv_path.open("r", newline="") as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader, start=1):
            values = [v.strip() for v in row if v.strip() != ""]

            if not values:
                continue

            if len(values) % 2 != 0:
                raise ValueError(
                    f"{csv_path.name} row {row_idx}: odd number of values, expected x,y pairs."
                )

            coords = np.array([int(float(v)) for v in values], dtype=np.int32).reshape(-1, 2)

            if len(coords) < 3:
                raise ValueError(
                    f"{csv_path.name} row {row_idx}: fewer than 3 points, invalid polygon."
                )

            polygons.append(coords)

    return polygons


def create_mask(image_shape: tuple[int, int], polygons: list[np.ndarray]) -> np.ndarray:
    h, w = image_shape
    mask = np.zeros((h, w), dtype=np.uint8)
    if polygons:
        cv2.fillPoly(mask, polygons, 255)
    return mask


def create_overlay(image_bgr: np.ndarray, polygons: list[np.ndarray], alpha: float = 0.35) -> np.ndarray:
    overlay = image_bgr.copy()
    if not polygons:
        return overlay

    filled = image_bgr.copy()
    cv2.fillPoly(filled, polygons, (0, 0, 255))
    overlay = cv2.addWeighted(filled, alpha, overlay, 1 - alpha, 0)

    for poly in polygons:
        cv2.polylines(overlay, [poly], True, (0, 255, 255), 2)

    return overlay


def polygon_area(poly: np.ndarray) -> float:
    return float(cv2.contourArea(poly.astype(np.float32)))


def polygon_centroid(poly: np.ndarray) -> tuple[int, int]:
    m = cv2.moments(poly.astype(np.float32))
    if m["m00"] == 0:
        x, y = poly.mean(axis=0)
        return int(x), int(y)
    return int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])


def process_split(split_dir: Path, out_root: Path, save_overlays: bool = True) -> dict:
    images_dir = out_root / "images"
    masks_dir = out_root / "masks"
    overlays_dir = out_root / "overlays"
    meta_dir = out_root / "meta"

    images_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    if save_overlays:
        overlays_dir.mkdir(parents=True, exist_ok=True)

    image_files = sorted([p for p in split_dir.iterdir() if p.suffix.lower() in VALID_IMAGE_EXTS])

    processed = 0
    missing_csv = 0
    total_mitoses = 0
    total_mask_pixels = 0
    items = []

    for image_path in image_files:
        stem = image_path.stem
        csv_path = split_dir / f"{stem}.csv"

        if not csv_path.exists():
            missing_csv += 1
            continue

        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            print(f"[WARN] Failed to read image: {image_path}")
            continue

        h, w = image_bgr.shape[:2]
        polygons = read_midesec_polygons(csv_path)
        mask = create_mask((h, w), polygons)

        out_image_path = images_dir / f"{stem}.png"
        out_mask_path = masks_dir / f"{stem}_mask.png"
        out_meta_path = meta_dir / f"{stem}.json"

        cv2.imwrite(str(out_image_path), image_bgr)
        cv2.imwrite(str(out_mask_path), mask)

        overlay_path_str = None
        if save_overlays:
            overlay = create_overlay(image_bgr, polygons)
            out_overlay_path = overlays_dir / f"{stem}_overlay.png"
            cv2.imwrite(str(out_overlay_path), overlay)
            overlay_path_str = str(out_overlay_path)

        areas = [polygon_area(p) for p in polygons]
        centroids = [polygon_centroid(p) for p in polygons]
        mask_pixels = int(np.count_nonzero(mask))

        meta = {
            "id": stem,
            "source_image": str(image_path),
            "source_csv": str(csv_path),
            "prepared_image": str(out_image_path),
            "prepared_mask": str(out_mask_path),
            "prepared_overlay": overlay_path_str,
            "image_width": w,
            "image_height": h,
            "mitosis_count": len(polygons),
            "mask_positive_pixels": mask_pixels,
            "coverage_ratio": float(mask_pixels / (h * w)),
            "average_polygon_area": float(np.mean(areas)) if areas else 0.0,
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

        with out_meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        items.append(
            {
                "id": stem,
                "image": str(out_image_path),
                "mask": str(out_mask_path),
                "meta": str(out_meta_path),
                "overlay": overlay_path_str,
                "mitosis_count": len(polygons),
            }
        )

        processed += 1
        total_mitoses += len(polygons)
        total_mask_pixels += mask_pixels

    summary = {
        "split_source": str(split_dir),
        "split_output": str(out_root),
        "processed_images": processed,
        "missing_csv": missing_csv,
        "total_mitoses": total_mitoses,
        "total_mask_pixels": total_mask_pixels,
        "average_mitoses_per_image": float(total_mitoses / processed) if processed else 0.0,
        "items": items,
    }

    with (out_root / "split_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare MiDeSeC BMP+CSV into trainable images/masks.")
    parser.add_argument("--train_dir", required=True, help="Path to MiDeSeC train folder")
    parser.add_argument("--test_dir", required=True, help="Path to MiDeSeC test folder")
    parser.add_argument(
        "--out_dir",
        default="backend/ml/model_b/data/midesec_prepared",
        help="Output root directory",
    )
    parser.add_argument(
        "--no_overlays",
        action="store_true",
        help="Disable overlay generation",
    )
    args = parser.parse_args()

    train_dir = Path(args.train_dir)
    test_dir = Path(args.test_dir)
    out_dir = Path(args.out_dir)

    if not train_dir.exists():
        raise FileNotFoundError(f"Train dir not found: {train_dir}")
    if not test_dir.exists():
        raise FileNotFoundError(f"Test dir not found: {test_dir}")

    save_overlays = not args.no_overlays

    train_summary = process_split(
        split_dir=train_dir,
        out_root=out_dir / "train",
        save_overlays=save_overlays,
    )
    test_summary = process_split(
        split_dir=test_dir,
        out_root=out_dir / "test",
        save_overlays=save_overlays,
    )

    full_summary = {
        "train": train_summary,
        "test": test_summary,
        "total_processed": train_summary["processed_images"] + test_summary["processed_images"],
        "total_mitoses": train_summary["total_mitoses"] + test_summary["total_mitoses"],
    }

    with (out_dir / "dataset_summary.json").open("w", encoding="utf-8") as f:
        json.dump(full_summary, f, indent=2)

    print("\n=== MiDeSeC Preparation Complete ===")
    print(f"Train processed: {train_summary['processed_images']}")
    print(f"Test processed:  {test_summary['processed_images']}")
    print(f"Total processed: {full_summary['total_processed']}")
    print(f"Total mitoses:   {full_summary['total_mitoses']}")
    print(f"Saved to:        {out_dir}")


if __name__ == "__main__":
    main()