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
        self.title("ParkGuard AI — Smart Parking Management")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # Header
        header = ctk.CTkFrame(self, height=50, fg_color="#1a1a2e")
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="\U0001f17f\ufe0f  ParkGuard AI",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#00d4aa").pack(side="left", padx=20)
        ctk.CTkLabel(header, text=f"Gate API: localhost:{GATE_SERVER_PORT}/gate",
                     font=ctk.CTkFont(size=12), text_color="#888").pack(side="right", padx=20)

        # Tabs
        self.tabview = ctk.CTkTabview(self, fg_color="#0f0f23",
                                       segmented_button_fg_color="#1a1a2e",
                                       segmented_button_selected_color="#00d4aa",
                                       segmented_button_selected_hover_color="#00b894")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_dashboard = self.tabview.add("\U0001f4ca Dashboard")
        self.tab_camera = self.tabview.add("\U0001f4f7 Camera")
        self.tab_clients = self.tabview.add("\U0001f465 Clients")
        self.tab_payments = self.tabview.add("\U0001f4b3 Payments")
        self.tab_logs = self.tabview.add("\U0001f4cb Logs")

        # Initialize tabs
        self.dashboard = DashboardTab(self.tab_dashboard)
        self.camera = CameraTab(self.tab_camera)
        self.clients = ClientsTab(self.tab_clients)
        self.payments = PaymentsTab(self.tab_payments)
        self.logs = LogsTab(self.tab_logs)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if hasattr(self, 'camera'):
            self.camera.stop_camera()
        self.destroy()
