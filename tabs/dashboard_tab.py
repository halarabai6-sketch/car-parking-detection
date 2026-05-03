"""ParkGuard AI — Dashboard Tab"""
import customtkinter as ctk
from database import get_stats, get_access_logs


class DashboardTab:
    def __init__(self, parent):
        self.parent = parent
        self._build()
        self.refresh()

    def _build(self):
        # Overview title
        ctk.CTkLabel(self.parent, text="Aperçu", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#888").pack(anchor="w", padx=20, pady=(15, 0))

        # Stats cards row
        self.cards_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.stat_cards = {}
        cards_data = [
            ("total_clients", "Clients Totaux", "\U0001f465", "#9b59b6"), # Purple
            ("paid_this_month", "Payé ce Mois", "\u2705", "#2ecc71"),     # Green
            ("unpaid_this_month", "Non Payé", "\u26a0\ufe0f", "#f1c40f"),      # Yellow
            ("today_entries", "Entrées du Jour", "\U0001f6d7", "#3498db"),   # Blue
            ("today_denied", "Refusés", "\U0001f6ab", "#e74c3c"),            # Red
        ]
        for i, (key, title, icon, color) in enumerate(cards_data):
            self.cards_frame.columnconfigure(i, weight=1)
            card = ctk.CTkFrame(self.cards_frame, fg_color="#1a1a2e", corner_radius=12)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            
            # Colored top border
            top_border = ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0)
            top_border.pack(fill="x", padx=15, pady=(10, 0))

            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(10, 0))
            val_lbl = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=32, weight="bold"),
                                   text_color=color)
            val_lbl.pack()
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12),
                         text_color="#aaa").pack(pady=(0, 15))
            self.stat_cards[key] = val_lbl

        # Recent logs section header & Refresh button
        logs_header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        logs_header_frame.pack(fill="x", padx=20)
        ctk.CTkLabel(logs_header_frame, text="Activité Récente",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#888").pack(side="left")
        ctk.CTkButton(logs_header_frame, text="\U0001f504 Actualiser", width=120,
                      fg_color="transparent", border_width=1, border_color="#f1c40f",
                      hover_color="#2a2a3e", text_color="#f1c40f",
                      command=self.refresh).pack(side="right")

        # Table header
        table_header = ctk.CTkFrame(self.parent, fg_color="#16213e", corner_radius=8)
        table_header.pack(fill="x", padx=20, pady=(10, 2))
        for i, (text, w) in enumerate([("Heure", 2), ("Matricule", 3), ("Client", 4), ("Portail", 2)]):
            table_header.columnconfigure(i, weight=w)
            ctk.CTkLabel(table_header, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#555").grid(row=0, column=i, padx=10, pady=5, sticky="w")

        self.logs_frame = ctk.CTkScrollableFrame(self.parent, fg_color="#1a1a2e", corner_radius=10)
        self.logs_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def refresh(self):
        stats = get_stats()
        for key, lbl in self.stat_cards.items():
            lbl.configure(text=str(stats.get(key, 0)))

        for w in self.logs_frame.winfo_children():
            w.destroy()

        logs = get_access_logs(limit=20)
        if not logs:
            ctk.CTkLabel(self.logs_frame, text="Aucune activité pour le moment.",
                         text_color="#666").pack(pady=20)
            return
        for log in logs:
            color = "#00b894" if log["gate_action"] == "OPEN" else "#d63031"
            icon = "\U0001f7e2" if log["gate_action"] == "OPEN" else "\U0001f534"
            row = ctk.CTkFrame(self.logs_frame, fg_color="#16213e", corner_radius=8)
            row.pack(fill="x", pady=2, padx=5)
            
            row.columnconfigure(0, weight=2)
            row.columnconfigure(1, weight=3)
            row.columnconfigure(2, weight=4)
            row.columnconfigure(3, weight=2)
            
            ctk.CTkLabel(row, text=f"{icon}  {log['timestamp'][:19]}",
                         font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=10, pady=8, sticky="w")
            ctk.CTkLabel(row, text=log.get("plate_number", "—"),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#e0e0e0").grid(row=0, column=1, padx=10, sticky="w")
            ctk.CTkLabel(row, text=log.get("client_name", "Inconnu"),
                         font=ctk.CTkFont(size=12), text_color="#aaa").grid(row=0, column=2, padx=10, sticky="w")
            ctk.CTkLabel(row, text=log["status"],
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=color).grid(row=0, column=3, padx=10, pady=8, sticky="w")
