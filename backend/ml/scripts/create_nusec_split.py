from pathlib import Path
import random
import csv

# processed training data from previous step
IMG_DIR = Path(r"backend/ml/processed/nusec/train/images")
MASK_DIR = Path(r"backend/ml/processed/nusec/train/masks_binary")

# output split file
OUT_CSV = Path(r"backend/ml/processed/nusec/nusec_split.csv")

VAL_RATIO = 0.2
SEED = 42

def main():
    img_files = sorted(IMG_DIR.glob("*.png"))
    mask_files = sorted(MASK_DIR.glob("*.png"))

    img_map = {f.name: f for f in img_files}
    mask_map = {f.name: f for f in mask_files}

    img_names = set(img_map.keys())
    mask_names = set(mask_map.keys())

    matched = sorted(img_names & mask_names)
    img_only = sorted(img_names - mask_names)
    mask_only = sorted(mask_names - img_names)

    print(f"Images found : {len(img_files)}")
    print(f"Masks found  : {len(mask_files)}")
    print(f"Matched      : {len(matched)}")
    print(f"Image only   : {len(img_only)}")
    print(f"Mask only    : {len(mask_only)}")

    if not matched:
        print("No matched files found.")
        return

    random.seed(SEED)
    random.shuffle(matched)

    val_count = int(len(matched) * VAL_RATIO)
    val_names = set(matched[:val_count])

    train_count = 0
    val_real_count = 0

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_path", "mask_path", "split"])

        for name in matched:
            split = "val" if name in val_names else "train"
            if split == "train":
                train_count += 1
            else:
                val_real_count += 1

            writer.writerow([
                str(img_map[name].as_posix()),
                str(mask_map[name].as_posix()),
                split
            ])

    print(f"\nTrain samples: {train_count}")
    print(f"Val samples  : {val_real_count}")
    print(f"\nCSV saved to: {OUT_CSV}")

    print("\nSample entries:")
    for name in matched[:5]:
        split = "val" if name in val_names else "train"
        print(f"  {name} -> {split}")

if __name__ == "__main__":
    main()