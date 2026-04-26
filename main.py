"""
ParkGuard AI — Main Entry Point
Standalone desktop parking management application.
"""
import customtkinter as ctk
import threading
from database import init_db
from gate_server import start_gate_server
from app_gui import ParkGuardApp

def main():
    init_db()
    start_gate_server()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ParkGuardApp()
    app.mainloop()

if __name__ == "__main__":
    main()
