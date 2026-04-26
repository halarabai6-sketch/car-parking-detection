"""ParkGuard AI — Dashboard Tab"""
import customtkinter as ctk
from database import get_stats, get_access_logs


class DashboardTab:
    def __init__(self, parent):
        self.parent = parent
        self._build()
        self.refresh()

    def _build(self):
        # Stats cards row
        self.cards_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=20, pady=20)

        self.stat_cards = {}
        cards_data = [
            ("total_clients", "Total Clients", "\U0001f465", "#6c5ce7"),
            ("paid_this_month", "Paid This Month", "\u2705", "#00b894"),
            ("unpaid_this_month", "Unpaid", "\u26a0\ufe0f", "#fdcb6e"),
            ("today_entries", "Entries Today", "\U0001f6d7", "#0984e3"),
            ("today_denied", "Denied Today", "\U0001f6ab", "#d63031"),
        ]
        for i, (key, title, icon, color) in enumerate(cards_data):
            self.cards_frame.columnconfigure(i, weight=1)
            card = ctk.CTkFrame(self.cards_frame, fg_color="#1a1a2e", corner_radius=12)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(15, 5))
            val_lbl = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=32, weight="bold"),
                                   text_color=color)
            val_lbl.pack()
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12),
                         text_color="#aaa").pack(pady=(0, 15))
            self.stat_cards[key] = val_lbl

        # Refresh button
        ctk.CTkButton(self.parent, text="\U0001f504 Refresh", width=120,
                      fg_color="#00d4aa", hover_color="#00b894", text_color="#000",
                      command=self.refresh).pack(pady=(0, 10))

        # Recent logs
        ctk.CTkLabel(self.parent, text="Recent Activity",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20)
        self.logs_frame = ctk.CTkScrollableFrame(self.parent, fg_color="#1a1a2e", corner_radius=10)
        self.logs_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))

    def refresh(self):
        stats = get_stats()
        for key, lbl in self.stat_cards.items():
            lbl.configure(text=str(stats.get(key, 0)))

        for w in self.logs_frame.winfo_children():
            w.destroy()

        logs = get_access_logs(limit=20)
        if not logs:
            ctk.CTkLabel(self.logs_frame, text="No activity yet.",
                         text_color="#666").pack(pady=20)
            return
        for log in logs:
            color = "#00b894" if log["gate_action"] == "OPEN" else "#d63031"
            icon = "\U0001f7e2" if log["gate_action"] == "OPEN" else "\U0001f534"
            row = ctk.CTkFrame(self.logs_frame, fg_color="#16213e", corner_radius=8)
            row.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(row, text=f"{icon}  {log['timestamp'][:19]}",
                         font=ctk.CTkFont(size=12)).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=log.get("plate_number", "—"),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#e0e0e0").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=log.get("client_name", "Unknown"),
                         font=ctk.CTkFont(size=12), text_color="#aaa").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=log["status"],
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=color).pack(side="right", padx=15, pady=8)
