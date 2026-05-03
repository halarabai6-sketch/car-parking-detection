"""ParkGuard AI — Camera & Live Detection Tab
Continuous video stream with real-time plate detection.
"""
import customtkinter as ctk
import cv2
import threading
import time
import re
from PIL import Image
from detector import PlateDetector
from database import get_client_by_plate, check_payment_status, log_access
from gate_server import gate_state
from config import (CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,
                    DETECTION_INTERVAL_MS, DETECTION_COOLDOWN_S)


class CameraTab:
    def __init__(self, parent):
        self.parent = parent
        self.detector = PlateDetector()
        self.cap = None
        self.running = False
        self.current_frame = None
        self._after_id = None
        self._model_loaded = False

        # --- Live detection state ---
        self._detect_thread = None
        self._detect_lock = threading.Lock()
        self._latest_detections = []       # shared between threads
        self._recent_plates = {}           # plate_text -> timestamp (cooldown tracker)
        self._last_plate_seen_time = 0
        self._is_gate_open_for_car = False

        self._build()

    def _build(self):
        # Top controls
        ctrl = ctk.CTkFrame(self.parent, fg_color="transparent")
        ctrl.pack(fill="x", padx=15, pady=10)

        self.btn_start = ctk.CTkButton(ctrl, text="\u25b6 Démarrer Caméra", width=160,
                                        fg_color="#00d4aa", hover_color="#00b894",
                                        text_color="#000", command=self.start_camera)
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(ctrl, text="\u23f9 Arrêter", width=100,
                                       fg_color="#d63031", hover_color="#c0392b",
                                       command=self.stop_camera, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.status_lbl = ctk.CTkLabel(ctrl, text="Caméra arrêtée", text_color="#888",
                                        font=ctk.CTkFont(size=12))
        self.status_lbl.pack(side="right", padx=10)

        # Live indicator
        self.live_indicator = ctk.CTkLabel(ctrl, text="", font=ctk.CTkFont(size=12, weight="bold"),
                                            text_color="#d63031")
        self.live_indicator.pack(side="right", padx=5)

        # Main content: camera + result panel
        content = ctk.CTkFrame(self.parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # Camera feed
        cam_frame = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=12)
        cam_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.cam_label = ctk.CTkLabel(cam_frame, text="Flux de Caméra\n\nCliquez sur 'Démarrer Caméra' pour commencer",
                                       font=ctk.CTkFont(size=16), text_color="#555")
        self.cam_label.pack(expand=True, fill="both", padx=10, pady=10)

        # Result panel
        result_frame = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=12)
        result_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(result_frame, text="Résultat de Détection",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#00d4aa").pack(pady=(20, 15))

        # Gate status indicator
        self.gate_indicator = ctk.CTkFrame(result_frame, width=120, height=120,
                                            corner_radius=60, fg_color="#333")
        self.gate_indicator.pack(pady=10)
        self.gate_indicator.pack_propagate(False)
        self.gate_icon = ctk.CTkLabel(self.gate_indicator, text="\u23f8",
                                       font=ctk.CTkFont(size=40))
        self.gate_icon.place(relx=0.5, rely=0.5, anchor="center")

        self.gate_lbl = ctk.CTkLabel(result_frame, text="EN ATTENTE",
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color="#888")
        self.gate_lbl.pack(pady=(5, 15))

        sep = ctk.CTkFrame(result_frame, height=2, fg_color="#333")
        sep.pack(fill="x", padx=20, pady=5)

        # Detection info labels
        info_data = [("Matricule:", "plate"), ("Client:", "client"),
                     ("Statut:", "status"), ("Paiement:", "payment")]
        self.info_labels = {}
        for title, key in info_data:
            row = ctk.CTkFrame(result_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=13),
                         text_color="#888", width=80, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(size=13, weight="bold"),
                               anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            self.info_labels[key] = lbl

        # --- Recent detections log ---
        sep2 = ctk.CTkFrame(result_frame, height=2, fg_color="#333")
        sep2.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(result_frame, text="Plaques Récentes",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#00d4aa").pack(pady=(5, 5))

        self.recent_list = ctk.CTkScrollableFrame(result_frame, fg_color="#0f0f23",
                                                   height=150)
        self.recent_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── Camera lifecycle ───────────────────────────────────────────

    def start_camera(self):
        if self.running:
            return
        self.status_lbl.configure(text="Chargement du modèle...", text_color="#fdcb6e")
        self.parent.update()

        def _load_and_start():
            if not self._model_loaded:
                ok, msg = self.detector.load()
                self._model_loaded = ok
                if not ok:
                    self.status_lbl.configure(text=f"Erreur modèle: {msg}", text_color="#d63031")
                    return

            self.cap = cv2.VideoCapture(CAMERA_INDEX)
            if not self.cap.isOpened():
                self.status_lbl.configure(text="Impossible d'ouvrir la caméra!", text_color="#d63031")
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.running = True
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.status_lbl.configure(text="\U0001f7e2 En direct — détection de plaques",
                                      text_color="#00b894")
            self.live_indicator.configure(text="\u25cf EN DIRECT", text_color="#d63031")

            # Start the frame display loop
            self._update_frame()
            # Start the background detection thread
            self._start_detection_thread()

        threading.Thread(target=_load_and_start, daemon=True).start()

    def stop_camera(self):
        self.running = False
        if self._after_id:
            self.parent.after_cancel(self._after_id)
            self._after_id = None
        # Wait for detection thread to finish
        if self._detect_thread and self._detect_thread.is_alive():
            self._detect_thread.join(timeout=2)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_lbl.configure(text="Caméra arrêtée", text_color="#888")
        self.live_indicator.configure(text="")
        self.cam_label.configure(image=None, text="Caméra arrêtée")

    # ── Frame display loop (main thread, ~30fps) ──────────────────

    def _update_frame(self):
        if not self.running or self.cap is None:
            return
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame

            # Overlay detections on the live frame (never freeze)
            with self._detect_lock:
                detections = list(self._latest_detections)

            display_frame = frame.copy()
            if detections:
                display_frame = self.detector.draw_detections(display_frame, detections)

            display = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(display)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img,
                                    size=(CAMERA_WIDTH, CAMERA_HEIGHT))
            self.cam_label.configure(image=ctk_img, text="")

        self._after_id = self.parent.after(30, self._update_frame)

    # ── Background detection thread ───────────────────────────────

    def _start_detection_thread(self):
        """Start a daemon thread that continuously runs detection."""
        self._detect_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._detect_thread.start()

    def _detection_loop(self):
        """Runs YOLO + OCR continuously on the latest frame."""
        interval_s = DETECTION_INTERVAL_MS / 1000.0

        while self.running:
            frame = self.current_frame
            if frame is None:
                time.sleep(0.1)
                continue

            frame_copy = frame.copy()
            try:
                detections = self.detector.detect(frame_copy)
            except Exception:
                detections = []

            # Update shared detection state
            with self._detect_lock:
                self._latest_detections = detections

            # Process detected plates (with cooldown deduplication)
            if detections:
                self._last_plate_seen_time = time.time()
                best = max(detections, key=lambda d: d["confidence"])
                plate = best["plate_text"]
                if plate and not self._is_on_cooldown(plate):
                    self._recent_plates[plate] = time.time()
                    # Schedule UI update + DB processing on main thread
                    try:
                        self.parent.after(0, lambda p=plate: self._process_plate(p))
                    except Exception:
                        pass
            else:
                # No plate in view — update status on main thread
                try:
                    self.parent.after(0, self._set_idle)
                except Exception:
                    pass
                
                # Auto-close delay logic
                if self._is_gate_open_for_car and self._last_plate_seen_time > 0:
                    if time.time() - self._last_plate_seen_time > 10.0:
                        gate_state.set("DENIED")
                        self._is_gate_open_for_car = False
                        self._last_plate_seen_time = 0
                        try:
                            self.parent.after(0, self._close_gate_ui)
                        except Exception:
                            pass

            # Sleep before next detection cycle
            time.sleep(interval_s)

    def _is_on_cooldown(self, plate_text):
        """Check if a plate was recently processed (within cooldown window)."""
        last_seen = self._recent_plates.get(plate_text)
        if last_seen is None:
            return False
        return (time.time() - last_seen) < DETECTION_COOLDOWN_S

    def _set_idle(self):
        """Reset result panel to idle (called from main thread)."""
        try:
            self.status_lbl.configure(text="\U0001f7e2 En direct — aucune plaque visible",
                                      text_color="#00b894")
        except Exception:
            pass

    def _close_gate_ui(self):
        """Reset result panel after auto-close."""
        try:
            self._update_result("—", "—", "—", "—", "IDLE")
            self.status_lbl.configure(text="\U0001f7e2 En direct — portail refermé (aucune plaque)",
                                      text_color="#00b894")
        except Exception:
            pass

    # ── Plate processing (runs on main thread) ────────────────────

    def _process_plate(self, plate_text):
        if not plate_text:
            self._update_result("???", "Impossible de lire la plaque", "—", "—", "DENIED")
            if not self._is_gate_open_for_car:
                gate_state.set("DENIED")
            log_access(plate_text, None, None, "ILLISIBLE", "DENIED")
            return

        # Validate Moroccan plate format
        if not re.match(r"^\d{1,5}-[A-Z]-\d{1,2}$", plate_text):
            self._update_result(plate_text, "FORMAT INVALIDE", "ILLISIBLE", "—", "DENIED")
            if not self._is_gate_open_for_car:
                gate_state.set("DENIED")
            log_access(plate_text, None, None, "ILLISIBLE", "DENIED")
            self.status_lbl.configure(text=f"\U0001f534 {plate_text} — FORMAT INVALIDE",
                                      text_color="#d63031")
            self._add_recent_entry(plate_text, "DENIED", "Format Invalide")
            return

        client = get_client_by_plate(plate_text)
        if client is None:
            self._update_result(plate_text, "NON ENREGISTRÉ", "NON AUTORISÉ", "—", "DENIED")
            if not self._is_gate_open_for_car:
                gate_state.set("DENIED")
            log_access(plate_text, None, None, "NON AUTORISÉ", "DENIED")
            self.status_lbl.configure(text=f"\U0001f534 {plate_text} — NON ENREGISTRÉ",
                                      text_color="#d63031")
            self._add_recent_entry(plate_text, "DENIED")
            return

        name = f"{client['first_name']} {client['last_name']}"
        paid = check_payment_status(client["id"])

        if paid:
            self._update_result(plate_text, name, "ENREGISTRÉ", "PAYÉ \u2705", "OPEN")
            gate_state.set("OPEN")
            self._is_gate_open_for_car = True
            log_access(plate_text, client["id"], name, "AUTORISÉ", "OPEN")
            self.status_lbl.configure(text=f"\U0001f7e2 {plate_text} — PORTAIL OUVERT pour {name}",
                                      text_color="#00b894")
            self._add_recent_entry(plate_text, "OPEN", name)
        else:
            self._update_result(plate_text, name, "ENREGISTRÉ", "NON PAYÉ \u274c", "DENIED")
            if not self._is_gate_open_for_car:
                gate_state.set("DENIED")
            log_access(plate_text, client["id"], name, "NON PAYÉ", "DENIED")
            self.status_lbl.configure(text=f"\U0001f7e1 {plate_text} — NON PAYÉ ({name})",
                                      text_color="#fdcb6e")
            self._add_recent_entry(plate_text, "UNPAID", name)

    def _update_result(self, plate, client, status, payment, gate_action):
        try:
            self.info_labels["plate"].configure(text=plate)
            self.info_labels["client"].configure(text=client)
            self.info_labels["status"].configure(text=status)
            self.info_labels["payment"].configure(text=payment)
            if gate_action == "OPEN":
                self.gate_indicator.configure(fg_color="#00b894")
                self.gate_icon.configure(text="\u2714")
                self.gate_lbl.configure(text="PORTAIL OUVERT", text_color="#00b894")
            elif gate_action == "DENIED":
                self.gate_indicator.configure(fg_color="#d63031")
                self.gate_icon.configure(text="\u2716")
                self.gate_lbl.configure(text="PORTAIL FERMÉ", text_color="#d63031")
            else:
                self.gate_indicator.configure(fg_color="#333")
                self.gate_icon.configure(text="\u23f8")
                self.gate_lbl.configure(text="EN ATTENTE", text_color="#888")
        except Exception:
            pass

    def _add_recent_entry(self, plate_text, action, name=None):
        """Add an entry to the recent plates log panel."""
        try:
            ts = time.strftime("%H:%M:%S")
            if action == "OPEN":
                color = "#00b894"
                icon = "\U0001f7e2"
            elif action == "UNPAID":
                color = "#fdcb6e"
                icon = "\U0001f7e1"
            else:
                color = "#d63031"
                icon = "\U0001f534"

            label_text = f"{icon} {ts}  {plate_text}"
            if name:
                label_text += f"  ({name})"

            entry = ctk.CTkLabel(self.recent_list, text=label_text,
                                  font=ctk.CTkFont(size=11),
                                  text_color=color, anchor="w")
            entry.pack(fill="x", padx=5, pady=1, anchor="nw")

            # Keep only the last 50 entries
            children = self.recent_list.winfo_children()
            if len(children) > 50:
                children[0].destroy()
        except Exception:
            pass
