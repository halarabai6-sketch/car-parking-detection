"""ParkGuard AI — Clients Management Tab"""
import customtkinter as ctk
from database import get_all_clients, add_client, update_client, delete_client, search_clients


class ClientsTab:
    def __init__(self, parent):
        self.parent = parent
        self._build()
        self.refresh()

    def _build(self):
        top = ctk.CTkFrame(self.parent, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(top, text="+ Add Client", width=130,
                      fg_color="#00d4aa", hover_color="#00b894",
                      text_color="#000", command=self._add_dialog).pack(side="left", padx=5)

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(top, textvariable=self.search_var,
                                     placeholder_text="\U0001f50d Search by name or plate...",
                                     width=250)
        search_entry.pack(side="left", padx=10)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        ctk.CTkButton(top, text="\U0001f504 Refresh", width=100,
                      fg_color="#6c5ce7", hover_color="#5b4cdb",
                      command=self.refresh).pack(side="right", padx=5)

        # Table header
        header = ctk.CTkFrame(self.parent, fg_color="#16213e", corner_radius=8)
        header.pack(fill="x", padx=15, pady=(0, 2))
        cols = [("Name", 3), ("Phone", 2), ("Email", 2), ("Plate", 2),
                ("Vehicle", 1), ("Actions", 2)]
        for i, (text, weight) in enumerate(cols):
            header.columnconfigure(i, weight=weight)
            ctk.CTkLabel(header, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#00d4aa").grid(row=0, column=i, padx=8, pady=8, sticky="w")

        self.list_frame = ctk.CTkScrollableFrame(self.parent, fg_color="#0f0f23")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        query = self.search_var.get().strip()
        clients = search_clients(query) if query else get_all_clients()
        if not clients:
            ctk.CTkLabel(self.list_frame, text="No clients found.",
                         text_color="#666", font=ctk.CTkFont(size=14)).pack(pady=30)
            return
        for c in clients:
            self._render_row(c)

    def _render_row(self, client):
        row = ctk.CTkFrame(self.list_frame, fg_color="#1a1a2e", corner_radius=8)
        row.pack(fill="x", pady=2, padx=2)
        for i in range(6):
            row.columnconfigure(i, weight=[3, 2, 2, 2, 1, 2][i])

        name = f"{client['first_name']} {client['last_name']}"
        values = [name, client.get("phone", "—"), client.get("email", "—"),
                  client["plate_number"], client.get("vehicle_type", "—")]
        for i, val in enumerate(values):
            ctk.CTkLabel(row, text=val or "—", font=ctk.CTkFont(size=12),
                         anchor="w").grid(row=0, column=i, padx=8, pady=10, sticky="w")

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        ctk.CTkButton(actions, text="Edit", width=55, height=28,
                      fg_color="#0984e3", hover_color="#0873c4", font=ctk.CTkFont(size=11),
                      command=lambda c=client: self._edit_dialog(c)).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="Delete", width=55, height=28,
                      fg_color="#d63031", hover_color="#c0392b", font=ctk.CTkFont(size=11),
                      command=lambda c=client: self._delete_confirm(c)).pack(side="left", padx=2)

    def _parse_plate(self, plate_str):
        """Parse a plate string like '12345-A-67' into 3 parts."""
        parts = plate_str.replace("|", "-").replace(" ", "").split("-")
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        return plate_str, "", ""

    def _add_dialog(self):
        self._open_form("Add New Client", {}, self._save_new)

    def _edit_dialog(self, client):
        self._open_form("Edit Client", client, lambda data: self._save_edit(client["id"], data))

    def _open_form(self, title, data, on_save):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(title)
        dialog.geometry("450x560")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#00d4aa").pack(pady=(15, 10))

        fields = {}

        # Regular text fields
        for label, key in [("First Name", "first_name"), ("Last Name", "last_name"),
                           ("Phone", "phone"), ("Email", "email")]:
            ctk.CTkLabel(dialog, text=label, font=ctk.CTkFont(size=12),
                         anchor="w").pack(fill="x", padx=30, pady=(4, 0))
            entry = ctk.CTkEntry(dialog, width=380)
            entry.insert(0, data.get(key, ""))
            entry.pack(padx=30, pady=(0, 2))
            fields[key] = entry

        # --- Plate Number: 3 fields for Moroccan format ---
        ctk.CTkLabel(dialog, text="Plate Number  (e.g. 78904 - \u0647 - 6)",
                     font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=30, pady=(8, 0))

        plate_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        plate_frame.pack(padx=30, pady=(0, 2))

        # Parse existing plate if editing
        p1, p2, p3 = "", "", ""
        if data.get("plate_number"):
            p1, p2, p3 = self._parse_plate(data["plate_number"])

        plate_1 = ctk.CTkEntry(plate_frame, width=130, placeholder_text="Numbers",
                                font=ctk.CTkFont(size=14), justify="center")
        plate_1.insert(0, p1)
        plate_1.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(plate_frame, text=" - ", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#00d4aa").pack(side="left")

        plate_2 = ctk.CTkEntry(plate_frame, width=80, placeholder_text="Letter",
                                font=ctk.CTkFont(size=14), justify="center")
        plate_2.insert(0, p2)
        plate_2.pack(side="left", padx=5)

        ctk.CTkLabel(plate_frame, text=" - ", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#00d4aa").pack(side="left")

        plate_3 = ctk.CTkEntry(plate_frame, width=80, placeholder_text="Region",
                                font=ctk.CTkFont(size=14), justify="center")
        plate_3.insert(0, p3)
        plate_3.pack(side="left", padx=(5, 0))

        fields["plate_parts"] = (plate_1, plate_2, plate_3)

        # Vehicle type dropdown
        ctk.CTkLabel(dialog, text="Vehicle Type", font=ctk.CTkFont(size=12),
                     anchor="w").pack(fill="x", padx=30, pady=(8, 0))
        vehicle_menu = ctk.CTkComboBox(dialog, width=380,
                                        values=["Car", "Motorcycle", "Truck", "Van", "SUV", "Other"])
        vehicle_menu.set(data.get("vehicle_type", "Car"))
        vehicle_menu.pack(padx=30, pady=(0, 2))
        fields["vehicle_type"] = vehicle_menu

        # Error message label
        msg_lbl = ctk.CTkLabel(dialog, text="", text_color="#d63031", font=ctk.CTkFont(size=12))
        msg_lbl.pack(pady=5)

        # Save button
        def _do_save():
            # Build plate number from 3 parts
            pp1 = plate_1.get().strip()
            pp2 = plate_2.get().strip()
            pp3 = plate_3.get().strip()
            if not pp1:
                msg_lbl.configure(text="Plate number is required!")
                return
            plate_number = f"{pp1}-{pp2}-{pp3}" if pp2 or pp3 else pp1

            vals = {k: (e.get() if hasattr(e, 'get') else "") for k, e in fields.items() if k != "plate_parts"}
            vals["plate_number"] = plate_number

            if not fields["first_name"].get().strip() or not fields["last_name"].get().strip():
                msg_lbl.configure(text="First and last name are required!")
                return

            vals["first_name"] = fields["first_name"].get().strip()
            vals["last_name"] = fields["last_name"].get().strip()
            vals["phone"] = fields["phone"].get().strip()
            vals["email"] = fields["email"].get().strip()
            vals["vehicle_type"] = vehicle_menu.get()

            on_save(vals)
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="\u2714  Save Client", height=38, width=200,
                      fg_color="#00d4aa", hover_color="#00b894",
                      text_color="#000", font=ctk.CTkFont(size=14, weight="bold"),
                      command=_do_save).pack(pady=(5, 15))

    def _save_new(self, data):
        add_client(data["first_name"], data["last_name"], data["phone"],
                   data["email"], data["plate_number"], data.get("vehicle_type", "Car"))

    def _save_edit(self, client_id, data):
        update_client(client_id, data["first_name"], data["last_name"], data["phone"],
                      data["email"], data["plate_number"], data.get("vehicle_type", "Car"))

    def _delete_confirm(self, client):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Confirm Delete")
        dialog.geometry("350x160")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text=f"Delete {client['first_name']} {client['last_name']}?",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(25, 5))
        ctk.CTkLabel(dialog, text=f"Plate: {client['plate_number']}",
                     text_color="#aaa").pack(pady=5)
        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=15)
        ctk.CTkButton(btns, text="Cancel", width=100, fg_color="#555",
                      command=dialog.destroy).pack(side="left", padx=10)

        def _do_delete():
            delete_client(client["id"])
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(btns, text="Delete", width=100, fg_color="#d63031",
                      hover_color="#c0392b", command=_do_delete).pack(side="left", padx=10)
