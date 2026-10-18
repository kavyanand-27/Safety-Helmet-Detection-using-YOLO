import os
import glob
from collections import Counter
from PIL import Image

def inspect():
    classes = {0: 'hat (helmet)', 1: 'person (no helmet)'}
    total_boxes = Counter()
    splits = ['train', 'valid', 'test']
    
    print("=" * 60)
    print("DATASET INSPECTION & VERIFICATION REPORT")
    print("=" * 60)
    
    for split in splits:
        img_files = glob.glob(os.path.join(split, 'images', '*.*'))
        lbl_files = glob.glob(os.path.join(split, 'labels', '*.txt'))
        
        split_boxes = Counter()
        empty_files = 0
        invalid_lines = 0
        
        # Check matching stems
        img_stems = set(os.path.splitext(os.path.basename(f))[0] for f in img_files)
        lbl_stems = set(os.path.splitext(os.path.basename(f))[0] for f in lbl_files)
        
        missing_lbls = img_stems - lbl_stems
        missing_imgs = lbl_stems - img_stems
        
        for lf in lbl_files:
            with open(lf, 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            if not lines:
                empty_files += 1
            for line in lines:
                parts = line.split()
                if len(parts) != 5:
                    invalid_lines += 1
                    continue
                try:
                    cid = int(parts[0])
                    # coordinates: x_center, y_center, width, height (normalized 0 to 1)
                    coords = [float(x) for x in parts[1:]]
                    if any(c < 0.0 or c > 1.0 for c in coords):
                        invalid_lines += 1
                        continue
                    split_boxes[cid] += 1
                    total_boxes[cid] += 1
                except ValueError:
                    invalid_lines += 1

        print(f"\n[Split: {split.upper()}]")
        print(f"  Images: {len(img_files)}")
        print(f"  Label files: {len(lbl_files)}")
        print(f"  Unmatched images (no label file): {len(missing_lbls)}")
        print(f"  Unmatched labels (no image file): {len(missing_imgs)}")
        print(f"  Images with no annotations (negative samples): {empty_files}")
        print(f"  Invalid annotation lines: {invalid_lines}")
        print("  Bounding box count per class:")
        for cid in sorted(split_boxes.keys()):
            name = classes.get(cid, f"Class {cid}")
            print(f"    - Class {cid} ({name}): {split_boxes[cid]:,d} boxes")
        print(f"  Total boxes in {split}: {sum(split_boxes.values()):,d}")

    print("\n" + "=" * 60)
    print("OVERALL DATASET SUMMARY")
    print("=" * 60)
    for cid in sorted(total_boxes.keys()):
        name = classes.get(cid, f"Class {cid}")
        print(f"  - Class {cid} ({name}): {total_boxes[cid]:,d} boxes ({total_boxes[cid]/sum(total_boxes.values())*100:.2f}%)")
    print(f"  Total annotations across dataset: {sum(total_boxes.values()):,d}")

    # Inspect image resolutions on a sample
    print("\nSample image dimensions (first 5 from train):")
    train_imgs = glob.glob(os.path.join('train', 'images', '*.*'))[:5]
    for p in train_imgs:
        with Image.open(p) as img:
            print(f"  {os.path.basename(p)}: size={img.size}, mode={img.mode}")

if __name__ == '__main__':
    inspect()
