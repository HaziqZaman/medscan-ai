from pathlib import Path
from PIL import Image
import numpy as np

# =========================
# INPUT PATHS
# =========================
RAW_DIR = Path(r"C:\Users\Aisha\Downloads\Ankara University Datasets\NuSeC\test nuclei")
MASK_DIR = Path(r"C:\Users\Aisha\Downloads\Ankara University Datasets\NuSeC\mask of test nuclei")

# =========================
# OUTPUT PATHS
# =========================
OUT_IMG_DIR = Path(r"backend\ml\processed\nusec\test\images")
OUT_MASK_DIR = Path(r"backend\ml\processed\nusec\test\masks_binary")

EXTS = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"]

def get_files(folder):
    files = []
    for ext in EXTS:
        files.extend(folder.glob(f"*{ext}"))
    return sorted(files)

def save_image_as_png(src_path, dst_path):
    img = Image.open(src_path).convert("RGB")
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst_path)

def convert_mask_to_binary(src_path, dst_path):
    mask = Image.open(src_path)
    arr = np.array(mask)

    binary = (arr > 0).astype(np.uint8) * 255

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(binary).save(dst_path)

    return {
        "original_unique": int(len(np.unique(arr))),
        "binary_unique": np.unique(binary).tolist()
    }

def main():
    raw_files = get_files(RAW_DIR)
    mask_files = get_files(MASK_DIR)

    print(f"Raw images found : {len(raw_files)}")
    print(f"Masks found      : {len(mask_files)}")

    raw_map = {f.stem: f for f in raw_files}
    mask_map = {f.stem: f for f in mask_files}

    matched = sorted(set(raw_map.keys()) & set(mask_map.keys()))
    raw_only = sorted(set(raw_map.keys()) - set(mask_map.keys()))
    mask_only = sorted(set(mask_map.keys()) - set(raw_map.keys()))

    print(f"\nMatched pairs    : {len(matched)}")
    print(f"Raw only         : {len(raw_only)}")
    print(f"Mask only        : {len(mask_only)}")

    if not matched:
        print("No matched test pairs found.")
        return

    for i, name in enumerate(matched):
        raw_src = raw_map[name]
        mask_src = mask_map[name]

        img_dst = OUT_IMG_DIR / f"{name}.png"
        mask_dst = OUT_MASK_DIR / f"{name}.png"

        save_image_as_png(raw_src, img_dst)
        info = convert_mask_to_binary(mask_src, mask_dst)

        if i < 3:
            print(f"\n{name}")
            print(f"  original_unique: {info['original_unique']}")
            print(f"  binary_unique  : {info['binary_unique']}")
            print(f"  saved_image    : {img_dst}")
            print(f"  saved_mask     : {mask_dst}")

    print("\nDone.")
    print(f"Processed test images saved to: {OUT_IMG_DIR}")
    print(f"Binary test masks saved to   : {OUT_MASK_DIR}")

if __name__ == "__main__":
    main()