"""
Safety Helmet Detection - Real-time Computer Vision Demo
Course: U21AMP05 Computer Vision | Assessment II Mini Project
KPR Institute of Engineering and Technology

Supports:
- Webcam (e.g. --source 0)
- Video file (e.g. --source path/to/video.mp4)
- Single image or folder of images (e.g. --source test/images)
"""

import argparse
import os
import sys
import time
import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] Ultralytics is not installed. Please install it using: pip install ultralytics")
    sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Real-Time Safety Helmet Detection using YOLOv8")
    parser.add_argument(
        "--weights",
        type=str,
        default="runs/helmet_experiments/yolov8s/weights/best.pt",
        help="Path to trained YOLOv8 weights (e.g., best.pt)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="Input source: '0' for webcam, path to video file (.mp4, .avi), or path to image (.jpg, .png)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="Confidence threshold (default: 0.35)",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.45,
        help="NMS IoU threshold (default: 0.45)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Device to run on: 'cuda:0', 'cpu', or leave empty for auto",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save output video or annotated image",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="demo_outputs",
        help="Directory to save output files",
    )
    return parser.parse_args()


def draw_hud_and_boxes(frame, results, fps):
    """
    Renders bounding boxes with professional industrial safety HUD styling.
    Class 0: 'hat' (Helmet - Safe / Green)
    Class 1: 'person' (No Helmet / Worker - Alert / Red)
    """
    h, w, _ = frame.shape
    boxes = results.boxes

    helmet_count = 0
    violation_count = 0

    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = xyxy

            if cls_id == 0:  # hat / helmet
                color = (0, 200, 0)  # Bright Green
                label = f"HELMET {conf:.2f}"
                helmet_count += 1
            else:  # person / no helmet
                color = (0, 0, 220)  # Bright Red
                label = f"NO HELMET {conf:.2f}"
                violation_count += 1

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw label banner
            (lw, lh), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(
                frame,
                (x1, max(0, y1 - lh - 6)),
                (x1 + lw + 6, max(0, y1)),
                color,
                -1,
            )
            cv2.putText(
                frame,
                label,
                (x1 + 3, max(lh + 2, y1 - 3)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

    # Top Industrial HUD Banner
    hud_bg = frame.copy()
    cv2.rectangle(hud_bg, (0, 0), (w, 55), (20, 20, 20), -1)
    frame = cv2.addWeighted(hud_bg, 0.75, frame, 0.25, 0)

    # Status text
    status_text = "SAFETY HELMET MONITORING SYSTEM"
    cv2.putText(frame, status_text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    # Counts and FPS
    hud_info = f"FPS: {fps:4.1f} | Helmets: {helmet_count} | Violations: {violation_count}"
    cv2.putText(frame, hud_info, (15, 47), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

    # Compliance indicator badge
    if violation_count > 0:
        badge_text = "STATUS: VIOLATION DETECTED"
        badge_color = (0, 0, 220)
    else:
        badge_text = "STATUS: COMPLIANT"
        badge_color = (0, 180, 0)

    (bw, bh), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    badge_x = max(15, w - bw - 20)
    cv2.rectangle(frame, (badge_x - 5, 12), (badge_x + bw + 5, 42), badge_color, -1)
    cv2.putText(frame, badge_text, (badge_x, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

    return frame


def run_demo():
    args = parse_arguments()

    if not os.path.exists(args.weights):
        # Fallback check for pretrained yolov8n or yolov8s if custom weights not trained yet
        alt_paths = [
            "weights/best.pt",
            "yolov8n.pt",
            "yolov8s.pt",
        ]
        found = False
        for p in alt_paths:
            if os.path.exists(p):
                print(f"[INFO] Specified weights '{args.weights}' not found. Using fallback '{p}' instead.")
                args.weights = p
                found = True
                break
        if not found:
            print(f"[WARNING] Weight file '{args.weights}' does not exist yet.")
            print("[INFO] Please provide trained weights using: python demo.py --weights path/to/best.pt")
            print("[INFO] Loading base yolov8n.pt for interface demonstration...")
            args.weights = "yolov8n.pt"

    print(f"[INFO] Loading YOLO model from: {args.weights}")
    model = YOLO(args.weights)

    os.makedirs(args.output_dir, exist_ok=True)

    # Check if source is image or video/webcam
    source = args.source
    is_webcam = source.isdigit()
    is_image = False
    if not is_webcam:
        ext = os.path.splitext(source)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            is_image = True

    if is_image:
        print(f"[INFO] Processing single image: {source}")
        frame = cv2.imread(source)
        if frame is None:
            print(f"[ERROR] Could not read image from {source}")
            return

        t0 = time.time()
        results = model.predict(
            source=frame,
            conf=args.conf,
            iou=args.iou,
            device=args.device if args.device else None,
            verbose=False,
        )[0]
        inference_time = (time.time() - t0) * 1000.0
        fps = 1000.0 / max(inference_time, 1e-5)

        annotated_frame = draw_hud_and_boxes(frame, results, fps)

        out_path = os.path.join(args.output_dir, "annotated_" + os.path.basename(source))
        cv2.imwrite(out_path, annotated_frame)
        print(f"[SUCCESS] Saved annotated result to: {out_path}")
        print(f"[INFO] Inference latency: {inference_time:.2f} ms ({fps:.1f} FPS)")

        cv2.imshow("Safety Helmet Detection Demo - Press any key to exit", annotated_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    # Video or Webcam Stream
    cap_source = int(source) if is_webcam else source
    cap = cv2.VideoCapture(cap_source)
    if not cap.isOpened():
        print(f"[ERROR] Failed to open video source: {source}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    video_writer = None
    if args.save:
        out_video_path = os.path.join(args.output_dir, "helmet_detection_output.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(out_video_path, fourcc, src_fps, (width, height))
        print(f"[INFO] Recording demo video to: {out_video_path}")

    print("\n" + "=" * 60)
    print("DEMO ACTIVE - CONTROLS:")
    print(" - Press 'q' or 'ESC' to exit")
    print(" - Press 's' to save current snapshot frame")
    print("=" * 60 + "\n")

    fps_buffer = []
    frame_idx = 0

    while True:
        t_start = time.time()
        ret, frame = cap.read()
        if not ret:
            print("[INFO] End of video stream reached.")
            break

        results = model.predict(
            source=frame,
            conf=args.conf,
            iou=args.iou,
            device=args.device if args.device else None,
            verbose=False,
        )[0]

        t_end = time.time()
        frame_time = t_end - t_start
        instant_fps = 1.0 / max(frame_time, 1e-5)
        fps_buffer.append(instant_fps)
        if len(fps_buffer) > 30:
            fps_buffer.pop(0)
        avg_fps = float(np.mean(fps_buffer))

        annotated_frame = draw_hud_and_boxes(frame, results, avg_fps)

        if video_writer is not None:
            video_writer.write(annotated_frame)

        cv2.imshow("KPRIET - Safety Helmet Detection Live Demo", annotated_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            break
        elif key == ord("s"):
            snap_path = os.path.join(args.output_dir, f"snapshot_frame_{frame_idx}.jpg")
            cv2.imwrite(snap_path, annotated_frame)
            print(f"[SAVED] Snapshot saved to: {snap_path}")

        frame_idx += 1

    cap.release()
    if video_writer is not None:
        video_writer.release()
    cv2.destroyAllWindows()
    print("[INFO] Demo session closed.")


if __name__ == "__main__":
    run_demo()
