import json
import os

def build_notebook():
    nb = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {
                "provenance": [],
                "gpuType": "T4"
            },
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3"
            },
            "language_info": {
                "name": "python"
            },
            "accelerator": "GPU"
        },
        "cells": []
    }

    def add_md(source):
        nb["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in source.strip().split("\n")]
        })

    def add_code(source):
        nb["cells"].append({
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [line + "\n" for line in source.strip().split("\n")]
        })

    # Header
    add_md("""# KPR Institute of Engineering and Technology
## Department of Computer Science and Engineering
### Course: U21AMP05 & Computer Vision | Assessment II - Mini Project
**Project 6: Safety Helmet Detection using YOLO (Units III, V)**

**Experimental Objective:**
1. Train custom YOLO detectors on the Roboflow Safety Helmet dataset (`hat` = helmet, `person` = no helmet).
2. Compare two distinct YOLO architectures under identical experimental conditions:
   - **Detector 1:** YOLOv8n (Nano - lightweight, low latency)
   - **Detector 2:** YOLOv8s (Small - higher capacity backbone)
3. Evaluate both on the held-out test split (757 images).
4. Strictly measure real empirical metrics without fabrication:
   - Precision, Recall, mAP@0.5, mAP@0.5:0.95 (overall and per-class)
   - GPU & CPU Inference Speed (Latency in ms & FPS)
   - Training Time and Model File Size
5. Generate comparison tables, training curves, PR curves, and confusion matrices.
6. Export trained weights (`best.pt`) and evaluation artifacts for local deployment and demo.""")

    # Cell 1: Environment & GPU Verification
    add_md("## Step 1: Hardware & Environment Verification (T4 GPU)")
    add_code("""# Verify GPU allocation in Colab
!nvidia-smi

import torch
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
    print(f"Device Memory: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
else:
    raise SystemError("GPU not found! Please go to Runtime -> Change runtime type -> Hardware accelerator -> T4 GPU")""")

    # Cell 2: Install Ultralytics
    add_md("## Step 2: Install Ultralytics and Supporting Libraries")
    add_code("""!pip install -q ultralytics matplotlib seaborn pandas tabulate pillow

import ultralytics
ultralytics.checks()""")

    # Cell 3: Mount Google Drive or Upload Dataset
    add_md("""## Step 3: Dataset Setup & Extraction
You can provide the dataset in **one of two ways**:
* **Option A (Fastest & Recommended):** Upload `Safety-Helmet-Wearing-Dataset.v1i.yolov8.zip` to your **Google Drive**, then mount Drive.
* **Option B:** Upload directly to the Colab files pane (wait until the circle progress reaches 100%).

Run the cell below to extract and verify.""")
    add_code("""import os
import zipfile
import shutil
import glob
import yaml

EXTRACT_DIR = "/content/dataset"
LOCAL_ZIP = "/content/Safety-Helmet-Wearing-Dataset.v1i.yolov8.zip"
DRIVE_ZIP = "/content/drive/MyDrive/Safety-Helmet-Wearing-Dataset.v1i.yolov8.zip"

# Check if Google Drive is mounted or if file is in Drive
zip_source = None
if os.path.exists(LOCAL_ZIP):
    zip_source = LOCAL_ZIP
elif os.path.exists(DRIVE_ZIP):
    zip_source = DRIVE_ZIP
else:
    # Try mounting Google Drive automatically
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        if os.path.exists(DRIVE_ZIP):
            zip_source = DRIVE_ZIP
    except Exception:
        pass

if zip_source is None:
    raise FileNotFoundError(
        "Dataset ZIP not found!\\n"
        "Please do one of the following:\\n"
        "1. Upload 'Safety-Helmet-Wearing-Dataset.v1i.yolov8.zip' to Google Drive (MyDrive) and rerun, OR\\n"
        "2. Upload it directly to the Colab files pane and wait until the upload circle completes (100%)."
    )

file_size_mb = os.path.getsize(zip_source) / (1024 * 1024)
print(f"Found dataset archive at: {zip_source}")
print(f"File size: {file_size_mb:.2f} MB")

if file_size_mb < 300.0:
    raise ValueError(
        f"Incomplete upload detected! The zip file is only {file_size_mb:.2f} MB.\\n"
        f"The complete dataset archive is ~328 MB (343,857,766 bytes).\\n"
        f"Please delete the partial file (!rm -f {zip_source}) and re-upload, or place it in your Google Drive."
    )

os.makedirs(EXTRACT_DIR, exist_ok=True)
print(f"Extracting {zip_source} to {EXTRACT_DIR}...")

# Use native fast unzip command
!unzip -q -o "{zip_source}" -d "{EXTRACT_DIR}"
print("Extraction complete!")

# Create updated data.yaml with absolute paths
yaml_path = os.path.join(EXTRACT_DIR, "data.yaml")
dataset_config = {
    'train': os.path.join(EXTRACT_DIR, 'train', 'images'),
    'val': os.path.join(EXTRACT_DIR, 'valid', 'images'),
    'test': os.path.join(EXTRACT_DIR, 'test', 'images'),
    'nc': 2,
    'names': ['hat', 'person']
}

with open(yaml_path, 'w') as f:
    yaml.dump(dataset_config, f, default_flow_style=False)

print(f"Updated data.yaml created at: {yaml_path}")
with open(yaml_path, 'r') as f:
    print(f.read())""")

    # Cell 4: Verify dataset split counts and label statistics
    add_md("## Step 4: Verify Dataset Split Integrity & Class Balance")
    add_code("""from collections import Counter

classes = {0: 'hat (helmet)', 1: 'person (no helmet)'}
total_boxes = Counter()

print("=" * 60)
print("DATASET INTEGRITY & SPLIT VERIFICATION")
print("=" * 60)

for split in ['train', 'valid', 'test']:
    imgs = glob.glob(os.path.join(EXTRACT_DIR, split, 'images', '*.*'))
    lbls = glob.glob(os.path.join(EXTRACT_DIR, split, 'labels', '*.txt'))
    split_boxes = Counter()
    for lf in lbls:
        with open(lf, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    cid = int(parts[0])
                    split_boxes[cid] += 1
                    total_boxes[cid] += 1
    print(f"[{split.upper()}] Images: {len(imgs)} | Labels: {len(lbls)} | Boxes: {sum(split_boxes.values())}")
    for cid in sorted(split_boxes.keys()):
        print(f"   - Class {cid} ({classes[cid]}): {split_boxes[cid]:,d} boxes")

print("\\n[TOTAL ACROSS ALL SPLITS]")
for cid in sorted(total_boxes.keys()):
    print(f"   - Class {cid} ({classes[cid]}): {total_boxes[cid]:,d} boxes ({total_boxes[cid]/sum(total_boxes.values())*100:.2f}%)")""")

    # Cell 5: Experiment Parameters Definition
    add_md("""## Step 5: Experimental Hyperparameters
To ensure **strict scientific validity** and satisfy Assessment II requirements:
- Both models are trained on the **exact same training split** (5,280 images).
- Both models are validated on the **exact same validation split** (1,505 images).
- Both models are evaluated on the **exact same held-out test split** (757 images).
- Common hyperparameters:
  - Input resolution: `640x640`
  - Epochs: `25` (provides solid convergence within standard Colab runtime)
  - Batch size: `16`
  - Optimizer: `auto` (SGD/AdamW with weight decay)
  - Random seed: `42` (fixed reproducibility)
  - Deterministic training: `True`""")
    add_code("""# Define common experiment parameters
EPOCHS = 25
IMGSZ = 640
BATCH_SIZE = 16
SEED = 42
YAML_PATH = os.path.join(EXTRACT_DIR, "data.yaml")
PROJECT_DIR = "/content/runs/helmet_experiments"

os.makedirs(PROJECT_DIR, exist_ok=True)
print(f"Experiment Configuration:")
print(f" - Epochs: {EPOCHS}")
print(f" - Image Size: {IMGSZ}x{IMGSZ}")
print(f" - Batch Size: {BATCH_SIZE}")
print(f" - Random Seed: {SEED}")
print(f" - Dataset Config: {YAML_PATH}")
print(f" - Project Directory: {PROJECT_DIR}")""")

    # Cell 6: Experiment 1 - Train YOLOv8n
    add_md("## Step 6: Experiment 1 — Train YOLOv8n (Nano Detector)")
    add_code("""import time
from ultralytics import YOLO

print("=" * 60)
print("STARTING EXPERIMENT 1: YOLOv8n Training")
print("=" * 60)

model_n = YOLO("yolov8n.pt")

start_time_n = time.time()
train_results_n = model_n.train(
    data=YAML_PATH,
    epochs=EPOCHS,
    imgsz=IMGSZ,
    batch=BATCH_SIZE,
    seed=SEED,
    deterministic=True,
    device=0,
    project=PROJECT_DIR,
    name="yolov8n",
    exist_ok=True,
    save=True,
    plots=True,
    verbose=True
)
training_time_n = time.time() - start_time_n

print(f"\\nYOLOv8n Training Complete in {training_time_n/60:.2f} minutes ({training_time_n:.1f} seconds)")""")

    # Cell 7: Evaluate YOLOv8n on Held-out Test Split
    add_md("## Step 7: Evaluate YOLOv8n on Held-out Test Set")
    add_code("""print("Evaluating YOLOv8n on Test Split (757 images)...")
best_weights_n = os.path.join(PROJECT_DIR, "yolov8n", "weights", "best.pt")
val_model_n = YOLO(best_weights_n)

# Run validation on test split
test_metrics_n = val_model_n.val(
    data=YAML_PATH,
    split="test",
    imgsz=IMGSZ,
    batch=BATCH_SIZE,
    device=0,
    plots=True
)

# Extract actual metrics
p_n = float(test_metrics_n.box.p.mean())
r_n = float(test_metrics_n.box.r.mean())
map50_n = float(test_metrics_n.box.map50)
map50_95_n = float(test_metrics_n.box.map)

print(f"\\nYOLOv8n Test Set Evaluation Results:")
print(f" - Overall Precision:   {p_n:.4f}")
print(f" - Overall Recall:      {r_n:.4f}")
print(f" - Overall mAP@0.5:     {map50_n:.4f}")
print(f" - Overall mAP@0.5:0.95:{map50_95_n:.4f}")

# Per-class breakdown
for i, cname in enumerate(test_metrics_n.names.values()):
    cp = test_metrics_n.box.p[i]
    cr = test_metrics_n.box.r[i]
    cmap50 = test_metrics_n.box.ap50[i]
    print(f"   * Class '{cname}': Precision={cp:.4f}, Recall={cr:.4f}, mAP@0.5={cmap50:.4f}")""")

    # Cell 8: Experiment 2 - Train YOLOv8s
    add_md("## Step 8: Experiment 2 — Train YOLOv8s (Small Detector)")
    add_code("""print("=" * 60)
print("STARTING EXPERIMENT 2: YOLOv8s Training")
print("=" * 60)

model_s = YOLO("yolov8s.pt")

start_time_s = time.time()
train_results_s = model_s.train(
    data=YAML_PATH,
    epochs=EPOCHS,
    imgsz=IMGSZ,
    batch=BATCH_SIZE,
    seed=SEED,
    deterministic=True,
    device=0,
    project=PROJECT_DIR,
    name="yolov8s",
    exist_ok=True,
    save=True,
    plots=True,
    verbose=True
)
training_time_s = time.time() - start_time_s

print(f"\\nYOLOv8s Training Complete in {training_time_s/60:.2f} minutes ({training_time_s:.1f} seconds)")""")

    # Cell 9: Evaluate YOLOv8s on Held-out Test Split
    add_md("## Step 9: Evaluate YOLOv8s on Held-out Test Set")
    add_code("""print("Evaluating YOLOv8s on Test Split (757 images)...")
best_weights_s = os.path.join(PROJECT_DIR, "yolov8s", "weights", "best.pt")
val_model_s = YOLO(best_weights_s)

# Run validation on test split
test_metrics_s = val_model_s.val(
    data=YAML_PATH,
    split="test",
    imgsz=IMGSZ,
    batch=BATCH_SIZE,
    device=0,
    plots=True
)

# Extract actual metrics
p_s = float(test_metrics_s.box.p.mean())
r_s = float(test_metrics_s.box.r.mean())
map50_s = float(test_metrics_s.box.map50)
map50_95_s = float(test_metrics_s.box.map)

print(f"\\nYOLOv8s Test Set Evaluation Results:")
print(f" - Overall Precision:   {p_s:.4f}")
print(f" - Overall Recall:      {r_s:.4f}")
print(f" - Overall mAP@0.5:     {map50_s:.4f}")
print(f" - Overall mAP@0.5:0.95:{map50_95_s:.4f}")

# Per-class breakdown
for i, cname in enumerate(test_metrics_s.names.values()):
    cp = test_metrics_s.box.p[i]
    cr = test_metrics_s.box.r[i]
    cmap50 = test_metrics_s.box.ap50[i]
    print(f"   * Class '{cname}': Precision={cp:.4f}, Recall={cr:.4f}, mAP@0.5={cmap50:.4f}")""")

    # Cell 10: Rigorous Speed Benchmark (GPU and CPU FPS)
    add_md("""## Step 10: Measure Real Inference Speed & FPS (GPU vs CPU)
As explicitly requested by the assessment brief:
> *"Report precision, recall and mAP@0.5 per class, plus FPS on CPU and GPU."*

We benchmark both trained models across 100 test images in both GPU and CPU execution modes after warm-up.""")
    add_code("""import numpy as np

def benchmark_speed(model_path, test_image_paths, device='cuda:0', runs=100):
    model = YOLO(model_path)
    # Warmup
    for _ in range(10):
        _ = model(test_image_paths[0], device=device, verbose=False)
    
    latencies = []
    for i in range(min(runs, len(test_image_paths))):
        img_p = test_image_paths[i]
        t0 = time.time()
        res = model(img_p, device=device, verbose=False)
        t1 = time.time()
        latencies.append((t1 - t0) * 1000.0) # in ms
    
    mean_lat = np.mean(latencies)
    fps = 1000.0 / mean_lat
    return mean_lat, fps

sample_test_imgs = glob.glob(os.path.join(EXTRACT_DIR, "test", "images", "*.*"))[:100]

print("Benchmarking YOLOv8n Speed...")
lat_n_gpu, fps_n_gpu = benchmark_speed(best_weights_n, sample_test_imgs, device="cuda:0")
lat_n_cpu, fps_n_cpu = benchmark_speed(best_weights_n, sample_test_imgs, device="cpu")

print("Benchmarking YOLOv8s Speed...")
lat_s_gpu, fps_s_gpu = benchmark_speed(best_weights_s, sample_test_imgs, device="cuda:0")
lat_s_cpu, fps_s_cpu = benchmark_speed(best_weights_s, sample_test_imgs, device="cpu")

print("\\nSpeed Benchmark Results:")
print(f"YOLOv8n GPU: {lat_n_gpu:.2f} ms ({fps_n_gpu:.1f} FPS) | CPU: {lat_n_cpu:.2f} ms ({fps_n_cpu:.1f} FPS)")
print(f"YOLOv8s GPU: {lat_s_gpu:.2f} ms ({fps_s_gpu:.1f} FPS) | CPU: {lat_s_cpu:.2f} ms ({fps_s_cpu:.1f} FPS)")""")

    # Cell 11: Quantitative Comparison Table
    add_md("## Step 11: Empirical Model Comparison Table")
    add_code("""import pandas as pd
from tabulate import tabulate

size_mb_n = os.path.getsize(best_weights_n) / (1024 * 1024)
size_mb_s = os.path.getsize(best_weights_s) / (1024 * 1024)

# Number of parameters
params_n = sum(p.numel() for p in YOLO(best_weights_n).model.parameters())
params_s = sum(p.numel() for p in YOLO(best_weights_s).model.parameters())

comparison_data = [
    {
        "Metric": "Model Architecture",
        "YOLOv8n (Nano)": "YOLOv8n",
        "YOLOv8s (Small)": "YOLOv8s"
    },
    {
        "Metric": "Parameters (M)",
        "YOLOv8n (Nano)": f"{params_n / 1e6:.2f}M",
        "YOLOv8s (Small)": f"{params_s / 1e6:.2f}M"
    },
    {
        "Metric": "Model Weights Size (MB)",
        "YOLOv8n (Nano)": f"{size_mb_n:.2f} MB",
        "YOLOv8s (Small)": f"{size_mb_s:.2f} MB"
    },
    {
        "Metric": "Training Time (min)",
        "YOLOv8n (Nano)": f"{training_time_n / 60:.2f} min",
        "YOLOv8s (Small)": f"{training_time_s / 60:.2f} min"
    },
    {
        "Metric": "Overall Precision",
        "YOLOv8n (Nano)": f"{p_n:.4f}",
        "YOLOv8s (Small)": f"{p_s:.4f}"
    },
    {
        "Metric": "Overall Recall",
        "YOLOv8n (Nano)": f"{r_n:.4f}",
        "YOLOv8s (Small)": f"{r_s:.4f}"
    },
    {
        "Metric": "Overall mAP@0.5",
        "YOLOv8n (Nano)": f"{map50_n:.4f}",
        "YOLOv8s (Small)": f"{map50_s:.4f}"
    },
    {
        "Metric": "Overall mAP@0.5:0.95",
        "YOLOv8n (Nano)": f"{map50_95_n:.4f}",
        "YOLOv8s (Small)": f"{map50_95_s:.4f}"
    },
    {
        "Metric": "mAP@0.5 (hat / helmet)",
        "YOLOv8n (Nano)": f"{test_metrics_n.box.ap50[0]:.4f}",
        "YOLOv8s (Small)": f"{test_metrics_s.box.ap50[0]:.4f}"
    },
    {
        "Metric": "mAP@0.5 (person / no helmet)",
        "YOLOv8n (Nano)": f"{test_metrics_n.box.ap50[1]:.4f}",
        "YOLOv8s (Small)": f"{test_metrics_s.box.ap50[1]:.4f}"
    },
    {
        "Metric": "GPU Latency (ms)",
        "YOLOv8n (Nano)": f"{lat_n_gpu:.2f} ms",
        "YOLOv8s (Small)": f"{lat_s_gpu:.2f} ms"
    },
    {
        "Metric": "GPU Inference FPS",
        "YOLOv8n (Nano)": f"{fps_n_gpu:.1f} FPS",
        "YOLOv8s (Small)": f"{fps_s_gpu:.1f} FPS"
    },
    {
        "Metric": "CPU Latency (ms)",
        "YOLOv8n (Nano)": f"{lat_n_cpu:.2f} ms",
        "YOLOv8s (Small)": f"{lat_s_cpu:.2f} ms"
    },
    {
        "Metric": "CPU Inference FPS",
        "YOLOv8n (Nano)": f"{fps_n_cpu:.1f} FPS",
        "YOLOv8s (Small)": f"{fps_s_cpu:.1f} FPS"
    }
]

df_comp = pd.DataFrame(comparison_data)
print(tabulate(df_comp, headers="keys", tablefmt="fancy_grid", showindex=False))

# Save comparison dataframe to CSV
comp_csv_path = os.path.join(PROJECT_DIR, "detector_comparison_table.csv")
df_comp.to_csv(comp_csv_path, index=False)
print(f"\\nComparison table saved to: {comp_csv_path}")""")

    # Cell 12: Generate Comparative Visualizations
    add_md("## Step 12: Comparative Graphs & Training Curves")
    add_code("""import matplotlib.pyplot as plt

# Load results.csv for both runs
csv_n = os.path.join(PROJECT_DIR, "yolov8n", "results.csv")
csv_s = os.path.join(PROJECT_DIR, "yolov8s", "results.csv")

df_n = pd.read_csv(csv_n)
df_s = pd.read_csv(csv_s)
df_n.columns = [c.strip() for c in df_n.columns]
df_s.columns = [c.strip() for c in df_s.columns]

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. mAP@0.5 Progression
axes[0, 0].plot(df_n['epoch'], df_n['metrics/mAP50(B)'], 'b-o', label='YOLOv8n mAP@0.5', linewidth=2)
axes[0, 0].plot(df_s['epoch'], df_s['metrics/mAP50(B)'], 'r-s', label='YOLOv8s mAP@0.5', linewidth=2)
axes[0, 0].set_title('Validation mAP@0.5 vs. Epoch', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('Epoch', fontsize=12)
axes[0, 0].set_ylabel('mAP@0.5', fontsize=12)
axes[0, 0].legend(fontsize=12)
axes[0, 0].grid(True)

# 2. mAP@0.5:0.95 Progression
axes[0, 1].plot(df_n['epoch'], df_n['metrics/mAP50-95(B)'], 'b--o', label='YOLOv8n mAP@0.5:0.95', linewidth=2)
axes[0, 1].plot(df_s['epoch'], df_s['metrics/mAP50-95(B)'], 'r--s', label='YOLOv8s mAP@0.5:0.95', linewidth=2)
axes[0, 1].set_title('Validation mAP@0.5:0.95 vs. Epoch', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('Epoch', fontsize=12)
axes[0, 1].set_ylabel('mAP@0.5:0.95', fontsize=12)
axes[0, 1].legend(fontsize=12)
axes[0, 1].grid(True)

# 3. Training Box Loss
axes[1, 0].plot(df_n['epoch'], df_n['train/box_loss'], 'b-', label='YOLOv8n Train Box Loss', linewidth=2)
axes[1, 0].plot(df_s['epoch'], df_s['train/box_loss'], 'r-', label='YOLOv8s Train Box Loss', linewidth=2)
axes[1, 0].set_title('Training Bounding Box Loss vs. Epoch', fontsize=14, fontweight='bold')
axes[1, 0].set_xlabel('Epoch', fontsize=12)
axes[1, 0].set_ylabel('Box Loss', fontsize=12)
axes[1, 0].legend(fontsize=12)
axes[1, 0].grid(True)

# 4. Training Classification Loss
axes[1, 1].plot(df_n['epoch'], df_n['train/cls_loss'], 'b-', label='YOLOv8n Train Cls Loss', linewidth=2)
axes[1, 1].plot(df_s['epoch'], df_s['train/cls_loss'], 'r-', label='YOLOv8s Train Cls Loss', linewidth=2)
axes[1, 1].set_title('Training Classification Loss vs. Epoch', fontsize=14, fontweight='bold')
axes[1, 1].set_xlabel('Epoch', fontsize=12)
axes[1, 1].set_ylabel('Classification Loss', fontsize=12)
axes[1, 1].legend(fontsize=12)
axes[1, 1].grid(True)

plt.tight_layout()
comparison_plot_path = os.path.join(PROJECT_DIR, "yolov8n_vs_yolov8s_training_curves.png")
plt.savefig(comparison_plot_path, dpi=300)
plt.show()
print(f"Comparison curves saved to: {comparison_plot_path}")""")

    # Cell 13: Qualitative Visual Test Sample Comparison
    add_md("## Step 13: Qualitative Test Inference Comparison")
    add_code("""import cv2

test_samples = glob.glob(os.path.join(EXTRACT_DIR, "test", "images", "*.*"))[:4]
fig, axes = plt.subplots(len(test_samples), 2, figsize=(16, 4 * len(test_samples)))

for idx, img_path in enumerate(test_samples):
    # Predict with YOLOv8n
    res_n = val_model_n.predict(img_path, conf=0.35, verbose=False)[0]
    img_n = res_n.plot()[:, :, ::-1] # BGR to RGB
    
    # Predict with YOLOv8s
    res_s = val_model_s.predict(img_path, conf=0.35, verbose=False)[0]
    img_s = res_s.plot()[:, :, ::-1]
    
    axes[idx, 0].imshow(img_n)
    axes[idx, 0].set_title(f"YOLOv8n: Sample {idx+1} (Detections: {len(res_n.boxes)})", fontsize=12)
    axes[idx, 0].axis('off')
    
    axes[idx, 1].imshow(img_s)
    axes[idx, 1].set_title(f"YOLOv8s: Sample {idx+1} (Detections: {len(res_s.boxes)})", fontsize=12)
    axes[idx, 1].axis('off')

plt.tight_layout()
qual_plot_path = os.path.join(PROJECT_DIR, "qualitative_detections_comparison.png")
plt.savefig(qual_plot_path, dpi=300)
plt.show()
print(f"Qualitative detections saved to: {qual_plot_path}")""")

    # Cell 14: Package and Download Complete Experiment Results
    add_md("""## Step 14: Package & Download All Experiment Artifacts
This step bundles:
- `yolov8n/weights/best.pt` & `last.pt`
- `yolov8s/weights/best.pt` & `last.pt`
- Training logs, PR curves, Confusion matrices, F1 curves
- Comparative CSV and plots
into a single ZIP file (`Safety_Helmet_Detection_Experiment_Results.zip`) for easy download and project inclusion.""")
    add_code("""import json

# Export experiment summary json
summary_dict = {
    "yolov8n": {
        "parameters": params_n,
        "weights_size_mb": size_mb_n,
        "training_time_min": training_time_n / 60,
        "precision": p_n,
        "recall": r_n,
        "map50": map50_n,
        "map50_95": map50_95_n,
        "class_hat_map50": float(test_metrics_n.box.ap50[0]),
        "class_person_map50": float(test_metrics_n.box.ap50[1]),
        "gpu_latency_ms": lat_n_gpu,
        "gpu_fps": fps_n_gpu,
        "cpu_latency_ms": lat_n_cpu,
        "cpu_fps": fps_n_cpu
    },
    "yolov8s": {
        "parameters": params_s,
        "weights_size_mb": size_mb_s,
        "training_time_min": training_time_s / 60,
        "precision": p_s,
        "recall": r_s,
        "map50": map50_s,
        "map50_95": map50_95_s,
        "class_hat_map50": float(test_metrics_s.box.ap50[0]),
        "class_person_map50": float(test_metrics_s.box.ap50[1]),
        "gpu_latency_ms": lat_s_gpu,
        "gpu_fps": fps_s_gpu,
        "cpu_latency_ms": lat_s_cpu,
        "cpu_fps": fps_s_cpu
    }
}

json_summary_path = os.path.join(PROJECT_DIR, "experiment_results.json")
with open(json_summary_path, 'w') as f:
    json.dump(summary_dict, f, indent=4)
print(f"Summary JSON written to: {json_summary_path}")

# Zip everything in PROJECT_DIR
zip_output = "/content/Safety_Helmet_Detection_Experiment_Results.zip"
print(f"Creating archive {zip_output}...")
shutil.make_archive("/content/Safety_Helmet_Detection_Experiment_Results", 'zip', PROJECT_DIR)

print(f"Archive created successfully: {zip_output} ({os.path.getsize(zip_output)/(1024*1024):.2f} MB)")

# Trigger download if in Colab
try:
    from google.colab import files
    files.download(zip_output)
    print("Download popup triggered in Colab!")
except Exception as e:
    print(f"Download trigger note: {e}")""")

    output_path = "Safety_Helmet_Detection_YOLOv8_Training.ipynb"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Notebook successfully generated at: {output_path}")

if __name__ == "__main__":
    build_notebook()
