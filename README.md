# Safety Helmet Detection using YOLO (YOLOv8n vs YOLOv8s)

**Course:** U21AMP05 - Computer Vision  
**Assessment:** Assessment II - Case Study / Mini Project (40 Marks)  
**Institution:** KPR Institute of Engineering and Technology, Department of CSE  
**Academic Year:** 2026 - 2027  
**Project No. 6:** Safety Helmet Detection using YOLO (Units III, V)  

---

## 📌 Project Overview
Industrial workplace and road safety regulations strictly mandate the use of safety helmets/hard hats to prevent traumatic head injuries. This project implements and benchmarks an end-to-end Computer Vision pipeline using the **Ultralytics YOLOv8** family to detect:
1. `hat`: Workers/riders wearing safety helmets (Compliant / Safe).
2. `person`: Workers/riders without safety helmets (Non-compliant / Violation alert).

To adhere strictly to the assessment brief, we compare two distinct detector architectures under identical training parameters:
- **Primary Detector:** `YOLOv8n` (Nano - compact backbone, edge/drone-optimized)
- **Secondary Detector:** `YOLOv8s` (Small - increased backbone capacity and depth)

Both models are benchmarked empirically for:
- Precision, Recall, mAP@0.5, mAP@0.5:0.95 (overall and per-class)
- Inference Latency and Frames Per Second (FPS) on both GPU (NVIDIA T4) and CPU

---

## 📊 Dataset Specifications
- **Source:** Roboflow Universe (`Safety-Helmet-Wearing-Dataset.v1i.yolov8`)
- **Total Images:** 7,542
  - **Train Split:** 5,280 images (83,543 bounding boxes: 6,250 `hat`, 77,293 `person`)
  - **Validation Split:** 1,505 images (24,509 bounding boxes: 1,838 `hat`, 22,671 `person`)
  - **Test Split (Held-out):** 757 images (12,227 bounding boxes: 910 `hat`, 11,317 `person`)
- **Total Annotations:** 120,279 bounding boxes
- **Image Resolution:** 640 x 640 RGB
- **Integrity:** Zero missing labels, zero orphan images, 100% valid normalized coordinates.

---

## 🚀 Execution Workflow

### Step 1: Run Training on Google Colab (T4 GPU)
1. Open [Google Colab](https://colab.research.google.com).
2. Upload the notebook file: [`Safety_Helmet_Detection_YOLOv8_Training.ipynb`](Safety_Helmet_Detection_YOLOv8_Training.ipynb).
3. Ensure runtime is set to **T4 GPU** (`Runtime -> Change runtime type -> Hardware accelerator -> T4 GPU`).
4. Upload `Safety-Helmet-Wearing-Dataset.v1i.yolov8.zip` to Colab or Google Drive.
5. Click **Run All**.
   - The notebook trains `YOLOv8n` and `YOLOv8s` with identical seeds (`seed=42`, `imgsz=640`, `batch=16`).
   - Evaluates both models on the held-out test split (757 images).
   - Measures real FPS on GPU and CPU.
   - Plots comparative training curves and confusion matrices.
   - Automatically downloads `Safety_Helmet_Detection_Experiment_Results.zip`.

### Step 2: Extract Experiment Results Locally
Extract the downloaded `Safety_Helmet_Detection_Experiment_Results.zip` into the project root directory under `runs/helmet_experiments/`.
Run the comparison analysis:
```bash
python evaluate_and_compare.py
```

### Step 3: Launch the Live Demo
To run the interactive industrial safety helmet detection HUD:
```bash
# Webcam Demo (real-time stream with HUD and violation counter)
python demo.py --weights runs/helmet_experiments/yolov8s/weights/best.pt --source 0

# Video File Demo
python demo.py --weights runs/helmet_experiments/yolov8s/weights/best.pt --source sample_video.mp4 --save

# Single Image Demo
python demo.py --weights runs/helmet_experiments/yolov8s/weights/best.pt --source test/images/sample.jpg
```

**Demo Controls:**
- Press `q` or `ESC` to quit.
- Press `s` to save the current annotated frame snapshot.

---

## 📁 Repository Structure
```text
├── Safety-Helmet-Wearing-Dataset.v1i.yolov8.zip   # Full dataset archive (7,542 images)
├── Safety_Helmet_Detection_YOLOv8_Training.ipynb   # Complete Google Colab training notebook
├── generate_colab_notebook.py                     # Notebook generation script
├── inspect_dataset.py                             # Dataset validation & statistics script
├── evaluate_and_compare.py                        # Model comparison & visualization script
├── demo.py                                        # Real-time HUD detection application
├── data.yaml                                      # YOLOv8 dataset configuration
├── requirements.txt                               # Python dependencies
└── README.md                                      # Documentation & execution guide
```

---

## 📦 What to Submit (Assessment Checklist)
1. **Report PDF (12 to 20 pages):**
   - Title Page (Project Title, Team Roll Numbers, Course Info)
   - Problem Statement & Objectives
   - Dataset Analysis (7,542 images, 120,279 annotations, class distribution)
   - Methodology & Pipeline Block Diagram
   - Implementation Details & Parameters
   - Empirical Results & Comparison Tables (Precision, Recall, mAP50, mAP50-95, CPU/GPU FPS)
   - Failure Cases & Error Analysis (small objects, occlusions, side angles)
   - IEEE References & Team Contribution Table
2. **Code Submission:**
   - GitHub repo or Zip file containing this clean structure, `README.md`, `requirements.txt`, notebook, and demo script.
3. **Demo Video:**
   - 2 to 3 minute screen recording demonstrating the model detecting helmets in real-time.
