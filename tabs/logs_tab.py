"""ParkGuard AI — Access Logs Tab"""
import customtkinter as ctk
from database import get_access_logs


class LogsTab:
    def __init__(self, parent):
        self.parent = parent
        self._build()
        self.refresh()

    def _build(self):
        top = ctk.CTkFrame(self.parent, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(top, text="\U0001f4cb Access Logs",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#00d4aa").pack(side="left", padx=5)
        ctk.CTkButton(top, text="\U0001f504 Refresh", width=100,
                      fg_color="#6c5ce7", hover_color="#5b4cdb",
                      command=self.refresh).pack(side="right", padx=5)

        # Header
        header = ctk.CTkFrame(self.parent, fg_color="#16213e", corner_radius=8)
        header.pack(fill="x", padx=15, pady=(0, 2))
        for i, (text, w) in enumerate([("Time", 3), ("Plate", 2), ("Client", 2),
                                         ("Status", 2), ("Gate", 1)]):
            header.columnconfigure(i, weight=w)
            ctk.CTkLabel(header, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#00d4aa").grid(row=0, column=i, padx=8, pady=8, sticky="w")

        self.list_frame = ctk.CTkScrollableFrame(self.parent, fg_color="#0f0f23")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        logs = get_access_logs(limit=200)
        if not logs:
            ctk.CTkLabel(self.list_frame, text="No access logs yet.",
                         text_color="#666", font=ctk.CTkFont(size=14)).pack(pady=30)
            return
        for log in logs:
            self._render_row(log)

    def _render_row(self, log):
        row = ctk.CTkFrame(self.list_frame, fg_color="#1a1a2e", corner_radius=8)
        row.pack(fill="x", pady=1, padx=2)
        for i, w in enumerate([3, 2, 2, 2, 1]):
            row.columnconfigure(i, weight=w)

        gate_color = "#00b894" if log["gate_action"] == "OPEN" else "#d63031"
        status_color = "#00b894" if log["status"] == "AUTHORIZED" else (
            "#fdcb6e" if log["status"] == "UNPAID" else "#d63031")

        ts = log["timestamp"][:19] if log["timestamp"] else "—"
        values = [ts, log.get("plate_number") or "—", log.get("client_name") or "Unknown"]

        for i, val in enumerate(values):
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=11),
                         anchor="w").grid(row=0, column=i, padx=8, pady=8, sticky="w")

        ctk.CTkLabel(row, text=log["status"], font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=status_color, anchor="w").grid(row=0, column=3, padx=8, pady=8, sticky="w")

        icon = "\U0001f7e2" if log["gate_action"] == "OPEN" else "\U0001f534"
        ctk.CTkLabel(row, text=f"{icon} {log['gate_action']}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=gate_color).grid(row=0, column=4, padx=8, pady=8, sticky="w")
