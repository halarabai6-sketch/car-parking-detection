"""
ParkGuard AI — Gate Signal HTTP Server
Runs a tiny HTTP server in a background thread.
Embedded systems (Arduino, Raspberry Pi, etc.) can poll:
    GET http://<ip>:5555/gate  →  {"action": "OPEN"} or {"action": "IDLE"}
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import GATE_SERVER_PORT


class _GateState:
    """Shared gate state."""
    def __init__(self):
        self.action = "IDLE"  # OPEN, DENIED, IDLE
        self.lock = threading.Lock()

    def set(self, action):
        with self.lock:
            self.action = action

    def get(self):
        with self.lock:
            return self.action

    def get_and_reset(self):
        """Read the current action and reset to IDLE (one-shot)."""
        with self.lock:
            action = self.action
            self.action = "IDLE"
            return action


# Singleton gate state
gate_state = _GateState()


class _GateHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the gate signal endpoint."""

    def do_GET(self):
        if self.path == "/gate":
            action = gate_state.get_and_reset()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"action": action}).encode())
        elif self.path == "/gate/peek":
            # Peek without resetting
            action = gate_state.get()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"action": action}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress console logs


def start_gate_server():
    """Start the gate signal HTTP server in a daemon thread."""
    server = HTTPServer(("0.0.0.0", GATE_SERVER_PORT), _GateHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
