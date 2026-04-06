from pathlib import Path
from PIL import Image
import numpy as np

# =========================
# EXACT PATHS
# =========================
RAW_DIR = Path(r"C:\Users\Aisha\Downloads\Ankara University Datasets\NuSeC\train nuclei")
MASK_DIR = Path(r"C:\Users\Aisha\Downloads\Ankara University Datasets\NuSeC\mask of train nuclei")

# allowed image extensions
EXTS = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"]

def get_files(folder):
    files = []
    for ext in EXTS:
        files.extend(folder.glob(f"*{ext}"))
    return sorted(files)

def stem_map(files):
    return {f.stem: f for f in files}

def inspect_mask(mask_path):
    img = Image.open(mask_path)
    arr = np.array(img)

    return {
        "shape": arr.shape,
        "dtype": str(arr.dtype),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "unique_count": int(len(np.unique(arr))),
    }

def main():
    raw_files = get_files(RAW_DIR)
    mask_files = get_files(MASK_DIR)

    print(f"Raw images found : {len(raw_files)}")
    print(f"Masks found      : {len(mask_files)}")

    raw_map = stem_map(raw_files)
    mask_map = stem_map(mask_files)

    raw_names = set(raw_map.keys())
    mask_names = set(mask_map.keys())

    matched = sorted(raw_names & mask_names)
    raw_only = sorted(raw_names - mask_names)
    mask_only = sorted(mask_names - raw_names)

    print(f"\nMatched pairs    : {len(matched)}")
    print(f"Raw only         : {len(raw_only)}")
    print(f"Mask only        : {len(mask_only)}")

    if raw_only:
        print("\nSample raw-only files:")
        for name in raw_only[:5]:
            print(" ", name)

    if mask_only:
        print("\nSample mask-only files:")
        for name in mask_only[:5]:
            print(" ", name)

    if matched:
        print("\nInspecting first 3 matched masks:")
        for name in matched[:3]:
            info = inspect_mask(mask_map[name])
            print(f"\n{name}")
            for k, v in info.items():
                print(f"  {k}: {v}")

if __name__ == "__main__":
    main()