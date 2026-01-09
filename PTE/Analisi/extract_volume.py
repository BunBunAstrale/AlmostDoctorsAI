#!/usr/bin/env python3
"""
Extract image size and lesion size (in voxels) from NIfTI segmentation masks.

Mask labels:
0 = background
1 = lesion
2 = edema
"""

from pathlib import Path
import csv
import numpy as np
import nibabel as nib

# =========================
# HARD-CODED PARAMETERS
# =========================
INPUT_DIR = Path("lesion_masks")
OUTPUT_CSV = Path("lesion_voxels.csv")
LESION_LABEL = 1


# =========================
# UTILS
# =========================
def iter_nifti_files(folder: Path):
    for p in sorted(folder.rglob("*")):
        if p.is_file() and (p.name.endswith(".nii") or p.name.endswith(".nii.gz")):
            yield p


def extract_patient_id(nifti_path: Path) -> str:
    name = nifti_path.name
    if name.endswith(".nii.gz"):
        return name.replace(".nii.gz", "")
    if name.endswith(".nii"):
        return name.replace(".nii", "")
    return name


def count_lesion_voxels(seg: np.ndarray) -> int:
    return int(np.count_nonzero(seg == LESION_LABEL))


# =========================
# MAIN
# =========================
def main():

    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")

    results = []

    for nifti_path in iter_nifti_files(INPUT_DIR):

        print(f"Processing: {nifti_path.name}")

        img = nib.load(str(nifti_path))
        seg = img.get_fdata()
        seg = np.rint(seg).astype(np.int16)

        image_shape = seg.shape
        lesion_voxels = count_lesion_voxels(seg)

        patient_id = extract_patient_id(nifti_path)

        results.append((
            patient_id,
            str(nifti_path),
            image_shape,
            lesion_voxels
        ))

    # =========================
    # SAVE CSV
    # =========================
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "patient_id",
            "file_path",
            "image_shape",
            "lesion_voxels"
        ])
        for pid, path, shape, vox in results:
            writer.writerow([
                pid,
                path,
                str(shape),
                vox
            ])

    print(f"\nDONE ✓")
    print(f"Processed {len(results)} volumes")
    print(f"Results saved to: {OUTPUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
