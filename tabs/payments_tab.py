"""ParkGuard AI — Payments Management Tab"""
import customtkinter as ctk
from database import get_all_payments, add_payment, delete_payment, get_all_clients
from datetime import date


class PaymentsTab:
    def __init__(self, parent):
        self.parent = parent
        self._build()
        self.refresh()

    def _build(self):
        top = ctk.CTkFrame(self.parent, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(top, text="+ Record Payment", width=160,
                      fg_color="#00d4aa", hover_color="#00b894",
                      text_color="#000", command=self._add_dialog).pack(side="left", padx=5)
        ctk.CTkButton(top, text="\U0001f504 Refresh", width=100,
                      fg_color="#6c5ce7", hover_color="#5b4cdb",
                      command=self.refresh).pack(side="right", padx=5)

        # Header
        header = ctk.CTkFrame(self.parent, fg_color="#16213e", corner_radius=8)
        header.pack(fill="x", padx=15, pady=(0, 2))
        for i, (text, w) in enumerate([("Client", 3), ("Plate", 2), ("Amount", 1),
                                         ("Month", 2), ("Date", 2), ("", 1)]):
            header.columnconfigure(i, weight=w)
            ctk.CTkLabel(header, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#00d4aa").grid(row=0, column=i, padx=8, pady=8, sticky="w")

        self.list_frame = ctk.CTkScrollableFrame(self.parent, fg_color="#0f0f23")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        payments = get_all_payments()
        if not payments:
            ctk.CTkLabel(self.list_frame, text="No payments recorded.",
                         text_color="#666", font=ctk.CTkFont(size=14)).pack(pady=30)
            return
        for p in payments:
            self._render_row(p)

    def _render_row(self, payment):
        row = ctk.CTkFrame(self.list_frame, fg_color="#1a1a2e", corner_radius=8)
        row.pack(fill="x", pady=2, padx=2)
        for i, w in enumerate([3, 2, 1, 2, 2, 1]):
            row.columnconfigure(i, weight=w)

        name = f"{payment.get('first_name', '')} {payment.get('last_name', '')}"
        values = [name, payment.get("plate_number", "—"),
                  f"${payment['amount']:.2f}", payment["month_covered"],
                  payment["payment_date"]]
        for i, val in enumerate(values):
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=12),
                         anchor="w").grid(row=0, column=i, padx=8, pady=10, sticky="w")

        ctk.CTkButton(row, text="\U0001f5d1", width=35, height=28,
                      fg_color="#d63031", hover_color="#c0392b",
                      command=lambda: self._delete(payment["id"])).grid(
            row=0, column=5, padx=5, pady=5)

    def _delete(self, payment_id):
        delete_payment(payment_id)
        self.refresh()

    def _add_dialog(self):
        clients = get_all_clients()
        if not clients:
            dialog = ctk.CTkToplevel(self.parent)
            dialog.title("No Clients")
            dialog.geometry("300x130")
            dialog.grab_set()
            dialog.attributes("-topmost", True)
            ctk.CTkLabel(dialog, text="Add clients first!",
                         font=ctk.CTkFont(size=14)).pack(pady=30)
            ctk.CTkButton(dialog, text="OK", command=dialog.destroy).pack()
            return

        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Record Payment")
        dialog.geometry("420x400")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text="Record Payment",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#00d4aa").pack(pady=(20, 15))

        # Client selector
        ctk.CTkLabel(dialog, text="Client:", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", padx=30, pady=(5, 0))
        client_names = [f"{c['first_name']} {c['last_name']} ({c['plate_number']})" for c in clients]
        client_menu = ctk.CTkComboBox(dialog, values=client_names, width=350)
        client_menu.pack(padx=30, pady=(0, 8))

        # Amount
        ctk.CTkLabel(dialog, text="Amount:", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", padx=30, pady=(5, 0))
        amount_entry = ctk.CTkEntry(dialog, width=350, placeholder_text="e.g., 50.00")
        amount_entry.pack(padx=30, pady=(0, 8))

        # Month covered — Year + Month dropdowns
        ctk.CTkLabel(dialog, text="Month Covered:", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", padx=30, pady=(5, 0))

        month_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        month_frame.pack(padx=30, pady=(0, 8), fill="x")

        current_year = date.today().year
        current_month = date.today().month

        # Month names for display
        month_names = [
            "01 - January", "02 - February", "03 - March",
            "04 - April", "05 - May", "06 - June",
            "07 - July", "08 - August", "09 - September",
            "10 - October", "11 - November", "12 - December"
        ]

        year_values = [str(y) for y in range(current_year - 1, current_year + 3)]
        year_menu = ctk.CTkComboBox(month_frame, values=year_values, width=100)
        year_menu.set(str(current_year))
        year_menu.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(month_frame, text="/", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#00d4aa").pack(side="left", padx=5)

        month_menu = ctk.CTkComboBox(month_frame, values=month_names, width=200)
        month_menu.set(month_names[current_month - 1])
        month_menu.pack(side="left", padx=(10, 0))

        # Error label
        msg_lbl = ctk.CTkLabel(dialog, text="", text_color="#d63031",
                               font=ctk.CTkFont(size=12))
        msg_lbl.pack(pady=(5, 0))

        # Save button
        def _save():
            idx = client_names.index(client_menu.get()) if client_menu.get() in client_names else -1
            if idx < 0:
                msg_lbl.configure(text="Please select a client!")
                return
            try:
                amount = float(amount_entry.get())
            except ValueError:
                msg_lbl.configure(text="Please enter a valid amount!")
                return

            # Build YYYY-MM from dropdowns
            year = year_menu.get().strip()
            month_str = month_menu.get().strip()[:2]  # "01 - January" → "01"
            month_covered = f"{year}-{month_str}"

            add_payment(clients[idx]["id"], amount, month_covered)
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="\u2714  Save Payment", height=40, width=220,
                      fg_color="#00d4aa", hover_color="#00b894",
                      text_color="#000", font=ctk.CTkFont(size=14, weight="bold"),
                      command=_save).pack(pady=(10, 20))
