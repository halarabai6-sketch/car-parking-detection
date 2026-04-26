"""
ParkGuard AI — License Plate Detector
Uses YOLO for plate detection and EasyOCR for character recognition.
"""
import cv2
import numpy as np
from config import MODEL_PATH, CONFIDENCE_THRESHOLD, OCR_LANGUAGES


class PlateDetector:
    """Detects and reads license plates from video frames."""

    def __init__(self):
        self.model = None
        self.reader = None
        self._loaded = False

    def load(self):
        """Load YOLO model and OCR reader (call once at startup)."""
        if self._loaded:
            return True, "Already loaded."
        try:
            from ultralytics import YOLO
            self.model = YOLO(MODEL_PATH)
            import easyocr
            self.reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)
            self._loaded = True
            return True, "Model and OCR loaded successfully."
        except Exception as e:
            return False, f"Failed to load: {e}"

    @property
    def is_loaded(self):
        return self._loaded

    def detect(self, frame):
        """
        Run plate detection + OCR on a frame.
        Returns list of dicts: [{bbox, confidence, plate_text}, ...]
        """
        if not self._loaded:
            return []

        results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        detections = []

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])

                # Crop and read plate text
                plate_img = frame[y1:y2, x1:x2]
                plate_text = self._read_plate(plate_img)

                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": conf,
                    "plate_text": plate_text,
                })

        return detections

    def _read_plate(self, plate_img):
        """Extract text from a cropped plate image using OCR."""
        if plate_img is None or plate_img.size == 0:
            return ""

        try:
            # Pre-process for better OCR accuracy
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            # Up-scale small crops
            h, w = gray.shape
            if w < 200:
                scale = 200 / w
                gray = cv2.resize(gray, None, fx=scale, fy=scale,
                                  interpolation=cv2.INTER_CUBIC)
            # Denoise
            gray = cv2.bilateralFilter(gray, 11, 17, 17)
            # Adaptive threshold for varying lighting
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Run OCR on both preprocessed versions, pick the best
            results_gray = self.reader.readtext(gray, detail=1)
            results_thresh = self.reader.readtext(thresh, detail=1)

            # Merge and pick highest-confidence characters
            all_results = results_gray + results_thresh
            if not all_results:
                return ""

            # Sort by confidence and combine text
            all_results.sort(key=lambda r: r[0][0][0])  # Sort left-to-right
            best_text = ""
            best_conf = 0
            for group in [results_gray, results_thresh]:
                if group:
                    text = " ".join([r[1] for r in sorted(group, key=lambda r: r[0][0][0])])
                    avg_conf = sum(r[2] for r in group) / len(group)
                    if avg_conf > best_conf:
                        best_conf = avg_conf
                        best_text = text

            # Clean up the plate text
            cleaned = best_text.upper().strip()
            # Remove common OCR noise but keep alphanumeric and hyphens
            cleaned = "".join(c for c in cleaned if c.isalnum() or c == "-")
            return cleaned

        except Exception:
            return ""

    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on the frame."""
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            text = det["plate_text"] or "???"
            conf = det["confidence"]

            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 100), 2)
            # Label background
            label = f"{text} ({conf:.0%})"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 6, y1), (0, 255, 100), -1)
            cv2.putText(annotated, label, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        return annotated
