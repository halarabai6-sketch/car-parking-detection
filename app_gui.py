"""ParkGuard AI — Main Application Window"""
import customtkinter as ctk
from tabs.dashboard_tab import DashboardTab
from tabs.camera_tab import CameraTab
from tabs.clients_tab import ClientsTab
from tabs.payments_tab import PaymentsTab
from tabs.logs_tab import LogsTab
from config import GATE_SERVER_PORT


class ParkGuardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ParkGuide AI — Smart Parking Management")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # Main layout container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ──
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1a1a2e")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Logo / Title
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        icon_lbl = ctk.CTkLabel(logo_frame, text="\U0001f17f\ufe0f", font=ctk.CTkFont(size=24), width=25)
        icon_lbl.pack(side="left")
        
        text_lbl = ctk.CTkLabel(logo_frame, text="ParkGuide", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff")
        text_lbl.pack(side="left", padx=(5, 0))
        subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="AI Parking Management",
                                      font=ctk.CTkFont(size=11), text_color="#888")
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Navigation Header
        nav_label = ctk.CTkLabel(self.sidebar_frame, text="NAVIGATION",
                                 font=ctk.CTkFont(size=10, weight="bold"), text_color="#555")
        nav_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        # Nav Buttons
        self.nav_buttons = {}
        self.current_frame = None

        self._create_nav_button("dashboard", "\U0001f4ca Tableau de Bord", row=3)
        self._create_nav_button("camera", "\U0001f4f7 Caméra en Direct", row=4)
        self._create_nav_button("clients", "\U0001f465 Clients", row=5)
        self._create_nav_button("payments", "\U0001f4b3 Paiements", row=6, sticky="nw")
        self._create_nav_button("logs", "\U0001f4cb Historique d'Accès", row=7, sticky="nw")

        # Gate API Status at bottom of sidebar
        gate_api_label = ctk.CTkLabel(self.sidebar_frame, text=f"\U0001f310 API Portail: localhost:{GATE_SERVER_PORT}",
                                      font=ctk.CTkFont(size=10), text_color="#555")
        gate_api_label.grid(row=9, column=0, padx=20, pady=20, sticky="sw")

        # ── Main Content Area ──
        self.main_container = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        
        # We will pack frames into main_container
        self.frames = {}
        
        self.frames["dashboard"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["camera"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["clients"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["payments"] = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["logs"] = ctk.CTkFrame(self.main_container, fg_color="transparent")

        # Initialize tabs inside their respective frames
        self.dashboard = DashboardTab(self.frames["dashboard"])
        self.camera = CameraTab(self.frames["camera"])
        self.clients = ClientsTab(self.frames["clients"])
        self.payments = PaymentsTab(self.frames["payments"])
        self.logs = LogsTab(self.frames["logs"])

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Select default
        self.select_frame("dashboard")

    def _create_nav_button(self, name, text, row, sticky="w"):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, fg_color="transparent", 
                            text_color="#888", hover_color="#2a2a3e", anchor="w",
                            font=ctk.CTkFont(size=13), corner_radius=6,
                            command=lambda n=name: self.select_frame(n))
        btn.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        self.nav_buttons[name] = btn

    def select_frame(self, name):
        # Update button colors
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                # Active styling (matching the image: yellow text)
                btn.configure(fg_color="#2a2a3e", text_color="#fdcb6e")
            else:
                btn.configure(fg_color="transparent", text_color="#888")

        # Show selected frame
        if self.current_frame is not None:
            self.frames[self.current_frame].pack_forget()

        self.frames[name].pack(fill="both", expand=True)
        self.current_frame = name

    def _on_close(self):
        if hasattr(self, 'camera'):
            self.camera.stop_camera()
        self.destroy()
