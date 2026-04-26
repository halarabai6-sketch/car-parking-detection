"""ParkGuard AI — Camera & Detection Tab"""
import customtkinter as ctk
import cv2
import threading
from PIL import Image
from detector import PlateDetector
from database import get_client_by_plate, check_payment_status, log_access
from gate_server import gate_state
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, DETECTION_INTERVAL_MS


class CameraTab:
    def __init__(self, parent):
        self.parent = parent
        self.detector = PlateDetector()
        self.cap = None
        self.running = False
        self.auto_detect = False
        self.current_frame = None
        self._after_id = None
        self._detect_after_id = None
        self._model_loaded = False
        self._build()

    def _build(self):
        # Top controls
        ctrl = ctk.CTkFrame(self.parent, fg_color="transparent")
        ctrl.pack(fill="x", padx=15, pady=10)

        self.btn_start = ctk.CTkButton(ctrl, text="\u25b6 Start Camera", width=140,
                                        fg_color="#00d4aa", hover_color="#00b894",
                                        text_color="#000", command=self.start_camera)
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(ctrl, text="\u23f9 Stop", width=100,
                                       fg_color="#d63031", hover_color="#c0392b",
                                       command=self.stop_camera, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.btn_detect = ctk.CTkButton(ctrl, text="\U0001f50d Detect Now", width=130,
                                         fg_color="#6c5ce7", hover_color="#5b4cdb",
                                         command=self._run_detection, state="disabled")
        self.btn_detect.pack(side="left", padx=5)

        self.auto_var = ctk.BooleanVar(value=False)
        self.auto_switch = ctk.CTkSwitch(ctrl, text="Auto-Detect", variable=self.auto_var,
                                          command=self._toggle_auto,
                                          progress_color="#00d4aa")
        self.auto_switch.pack(side="left", padx=15)

        self.status_lbl = ctk.CTkLabel(ctrl, text="Camera stopped", text_color="#888",
                                        font=ctk.CTkFont(size=12))
        self.status_lbl.pack(side="right", padx=10)

        # Main content: camera + result panel
        content = ctk.CTkFrame(self.parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # Camera feed
        cam_frame = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=12)
        cam_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.cam_label = ctk.CTkLabel(cam_frame, text="Camera Feed\n\nClick 'Start Camera' to begin",
                                       font=ctk.CTkFont(size=16), text_color="#555")
        self.cam_label.pack(expand=True, fill="both", padx=10, pady=10)

        # Result panel
        result_frame = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=12)
        result_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(result_frame, text="Detection Result",
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

        self.gate_lbl = ctk.CTkLabel(result_frame, text="IDLE",
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color="#888")
        self.gate_lbl.pack(pady=(5, 15))

        sep = ctk.CTkFrame(result_frame, height=2, fg_color="#333")
        sep.pack(fill="x", padx=20, pady=5)

        # Detection info labels
        info_data = [("Plate:", "plate"), ("Client:", "client"),
                     ("Status:", "status"), ("Payment:", "payment")]
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

    def start_camera(self):
        if self.running:
            return
        self.status_lbl.configure(text="Loading model...", text_color="#fdcb6e")
        self.parent.update()

        def _load_and_start():
            if not self._model_loaded:
                ok, msg = self.detector.load()
                self._model_loaded = ok
                if not ok:
                    self.status_lbl.configure(text=f"Model error: {msg}", text_color="#d63031")
                    return

            self.cap = cv2.VideoCapture(CAMERA_INDEX)
            if not self.cap.isOpened():
                self.status_lbl.configure(text="Cannot open camera!", text_color="#d63031")
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.running = True
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.btn_detect.configure(state="normal")
            self.status_lbl.configure(text="\U0001f7e2 Camera running", text_color="#00b894")
            self._update_frame()

        threading.Thread(target=_load_and_start, daemon=True).start()

    def stop_camera(self):
        self.running = False
        self.auto_detect = False
        self.auto_var.set(False)
        if self._after_id:
            self.parent.after_cancel(self._after_id)
        if self._detect_after_id:
            self.parent.after_cancel(self._detect_after_id)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.btn_detect.configure(state="disabled")
        self.status_lbl.configure(text="Camera stopped", text_color="#888")
        self.cam_label.configure(image=None, text="Camera stopped")

    def _update_frame(self):
        if not self.running or self.cap is None:
            return
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(display)
            # Fit to label size
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(CAMERA_WIDTH, CAMERA_HEIGHT))
            self.cam_label.configure(image=ctk_img, text="")
        self._after_id = self.parent.after(30, self._update_frame)

    def _toggle_auto(self):
        self.auto_detect = self.auto_var.get()
        if self.auto_detect and self.running:
            self._auto_detect_loop()

    def _auto_detect_loop(self):
        if not self.auto_detect or not self.running:
            return
        self._run_detection()
        self._detect_after_id = self.parent.after(DETECTION_INTERVAL_MS, self._auto_detect_loop)

    def _run_detection(self):
        if self.current_frame is None:
            return
        frame = self.current_frame.copy()
        self.status_lbl.configure(text="\U0001f50d Detecting...", text_color="#fdcb6e")
        self.parent.update()

        def _detect():
            detections = self.detector.detect(frame)
            annotated = self.detector.draw_detections(frame, detections)
            # Show annotated frame
            display = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(display)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(CAMERA_WIDTH, CAMERA_HEIGHT))
            try:
                self.cam_label.configure(image=ctk_img, text="")
            except Exception:
                return

            if detections:
                best = max(detections, key=lambda d: d["confidence"])
                plate = best["plate_text"]
                self._process_plate(plate)
            else:
                self._update_result("—", "No plate detected", "—", "—", "IDLE")
                self.status_lbl.configure(text="\U0001f7e2 Camera running — no plate found",
                                          text_color="#00b894")

        threading.Thread(target=_detect, daemon=True).start()

    def _process_plate(self, plate_text):
        if not plate_text:
            self._update_result("???", "Could not read plate", "—", "—", "DENIED")
            gate_state.set("DENIED")
            log_access(plate_text, None, None, "UNREADABLE", "DENIED")
            return

        client = get_client_by_plate(plate_text)
        if client is None:
            self._update_result(plate_text, "NOT REGISTERED", "UNAUTHORIZED", "—", "DENIED")
            gate_state.set("DENIED")
            log_access(plate_text, None, None, "UNAUTHORIZED", "DENIED")
            self.status_lbl.configure(text=f"\U0001f534 {plate_text} — NOT REGISTERED",
                                      text_color="#d63031")
            return

        name = f"{client['first_name']} {client['last_name']}"
        paid = check_payment_status(client["id"])

        if paid:
            self._update_result(plate_text, name, "REGISTERED", "PAID \u2705", "OPEN")
            gate_state.set("OPEN")
            log_access(plate_text, client["id"], name, "AUTHORIZED", "OPEN")
            self.status_lbl.configure(text=f"\U0001f7e2 {plate_text} — GATE OPENED for {name}",
                                      text_color="#00b894")
        else:
            self._update_result(plate_text, name, "REGISTERED", "UNPAID \u274c", "DENIED")
            gate_state.set("DENIED")
            log_access(plate_text, client["id"], name, "UNPAID", "DENIED")
            self.status_lbl.configure(text=f"\U0001f7e1 {plate_text} — UNPAID ({name})",
                                      text_color="#fdcb6e")

    def _update_result(self, plate, client, status, payment, gate_action):
        try:
            self.info_labels["plate"].configure(text=plate)
            self.info_labels["client"].configure(text=client)
            self.info_labels["status"].configure(text=status)
            self.info_labels["payment"].configure(text=payment)
            if gate_action == "OPEN":
                self.gate_indicator.configure(fg_color="#00b894")
                self.gate_icon.configure(text="\u2714")
                self.gate_lbl.configure(text="GATE OPEN", text_color="#00b894")
            elif gate_action == "DENIED":
                self.gate_indicator.configure(fg_color="#d63031")
                self.gate_icon.configure(text="\u2716")
                self.gate_lbl.configure(text="GATE CLOSED", text_color="#d63031")
            else:
                self.gate_indicator.configure(fg_color="#333")
                self.gate_icon.configure(text="\u23f8")
                self.gate_lbl.configure(text="IDLE", text_color="#888")
        except Exception:
            pass
