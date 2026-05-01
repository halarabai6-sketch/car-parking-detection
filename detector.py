"""
ParkGuard AI — License Plate Detector
Uses YOLO for plate detection and a second YOLO model for character recognition.
"""
import cv2
import numpy as np
from config import MODEL_PATH, READER_MODEL_PATH, CONFIDENCE_THRESHOLD

# Mapping for Moroccan plate characters — the reader model stores Arabic letters as numeric codes
# We map them to Latin characters to match the database format (e.g. 'H' for 'ه')
CHAR_MAP = {
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    '10': 'A',  # Alif / أ
    '11': 'B',  # Ba / ب
    '12': 'J',  # Jim / ج
    '13': 'D',  # Dal / د
    '14': 'H',  # Ha / ه
    '15': 'W',  # Waw / و
    '16': 'T',  # Ta / ط
}


class PlateDetector:
    """Detects and reads license plates from video frames."""

    def __init__(self):
        self.model = None
        self.reader_model = None
        self._loaded = False

    def load(self):
        """Load YOLO detection model and YOLO reader model (call once at startup)."""
        if self._loaded:
            return True, "Already loaded."
        try:
            from ultralytics import YOLO
            self.model = YOLO(MODEL_PATH)
            self.reader_model = YOLO(READER_MODEL_PATH)
            self._loaded = True
            return True, "Detection and reader models loaded successfully."
        except Exception as e:
            return False, f"Failed to load: {e}"

    @property
    def is_loaded(self):
        return self._loaded

    def detect(self, frame):
        """
        Run plate detection + character reading on a frame.
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
        """Extract text from a cropped plate image using the YOLO reader model."""
        if plate_img is None or plate_img.size == 0:
            return ""

        try:
            # Pre-process for better detection
            h, w = plate_img.shape[:2]
            if w < 200:
                scale = 200 / w
                plate_img = cv2.resize(plate_img, None, fx=scale, fy=scale,
                                       interpolation=cv2.INTER_CUBIC)

            # Run the reader model on the cropped plate
            results = self.reader_model(plate_img, conf=0.3, verbose=False)

            if not results or results[0].boxes is None or len(results[0].boxes) == 0:
                return ""

            # Extract detected characters with their positions
            chars = []
            for box in results[0].boxes:
                x1 = float(box.xyxy[0][0])
                cls_id = int(box.cls[0])
                raw_label = self.reader_model.names[cls_id]
                char = CHAR_MAP.get(raw_label, raw_label)
                confidence = float(box.conf[0])
                # Mark if this character is one of the Moroccan letters (codes 10-16)
                is_letter = raw_label in [str(i) for i in range(10, 17)]
                chars.append({'x': x1, 'char': char, 'is_letter': is_letter})

            # Sort characters left-to-right by x position
            chars.sort(key=lambda c: c['x'])

            # Build the plate text with hyphens: [Numbers]-[Letter]-[Region]
            parts = []
            current_part = ""
            for c in chars:
                if c['is_letter']:
                    if current_part:
                        parts.append(current_part)
                    parts.append(c['char'])
                    current_part = ""
                else:
                    current_part += c['char']
            if current_part:
                parts.append(current_part)

            plate_text = "-".join(parts)

            # Clean up
            cleaned = plate_text.strip()
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
