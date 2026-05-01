"""
ParkGuard AI — Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Model ---
_model_dir = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(_model_dir, "yolov8n_plate.pt")          # Detects plate location
READER_MODEL_PATH = os.path.join(_model_dir, "PlateReaderyolo.pt")  # Reads characters on plate
CONFIDENCE_THRESHOLD = 0.4

# --- Database ---
DATABASE_PATH = os.path.join(BASE_DIR, "parking.db")

# --- Camera ---
CAMERA_INDEX = 0  # 0 = default webcam, change if you have multiple cameras
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# --- Detection ---
DETECTION_INTERVAL_MS = 1000  # Run detection every N milliseconds in live mode
DETECTION_COOLDOWN_S = 10     # Seconds before re-processing the same plate
OCR_LANGUAGES = ["en", "fr"]  # Languages for EasyOCR

# --- Gate Signal Server ---
GATE_SERVER_PORT = 5555  # HTTP port for embedded system to poll gate status
