"""
ParkGuard AI — Database Operations (SQLite)
Manages clients, payments, and access logs.
"""
import sqlite3
from datetime import date, datetime
from config import DATABASE_PATH


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            plate_number TEXT NOT NULL UNIQUE,
            vehicle_type TEXT DEFAULT 'Car',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date DATE NOT NULL,
            month_covered TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT,
            client_id INTEGER,
            client_name TEXT,
            status TEXT NOT NULL,
            gate_action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
        )
    """)

    conn.commit()
    conn.close()


# ── Client Operations ──────────────────────────────────────────────

def add_client(first_name, last_name, phone, email, plate_number, vehicle_type="Car"):
    """Add a new client. Returns (success: bool, message: str)."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO clients (first_name, last_name, phone, email, plate_number, vehicle_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (first_name.strip(), last_name.strip(), phone.strip(),
             email.strip(), plate_number.upper().strip().replace(" ", ""),
             vehicle_type.strip())
        )
        conn.commit()
        return True, "Client added successfully."
    except sqlite3.IntegrityError:
        return False, "A client with this plate number already exists."
    finally:
        conn.close()


def get_all_clients():
    """Return all active clients as list of dicts."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM clients WHERE active = 1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client_by_id(client_id):
    """Return a single client by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_client_by_plate(plate_number):
    """Look up an active client by plate number."""
    cleaned = plate_number.upper().strip().replace(" ", "").replace("-", "")
    conn = get_db()
    # Try exact match first
    row = conn.execute(
        "SELECT * FROM clients WHERE REPLACE(REPLACE(plate_number, ' ', ''), '-', '') = ? AND active = 1",
        (cleaned,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_client(client_id, first_name, last_name, phone, email, plate_number, vehicle_type):
    """Update client information."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE clients SET first_name=?, last_name=?, phone=?, email=?, "
            "plate_number=?, vehicle_type=? WHERE id=?",
            (first_name.strip(), last_name.strip(), phone.strip(), email.strip(),
             plate_number.upper().strip().replace(" ", ""), vehicle_type.strip(), client_id)
        )
        conn.commit()
        return True, "Client updated."
    except sqlite3.IntegrityError:
        return False, "Plate number already taken by another client."
    finally:
        conn.close()


def delete_client(client_id):
    """Soft-delete a client (set active = 0)."""
    conn = get_db()
    conn.execute("UPDATE clients SET active = 0 WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()


def search_clients(query):
    """Search clients by name or plate number."""
    conn = get_db()
    q = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM clients WHERE active = 1 AND "
        "(first_name LIKE ? OR last_name LIKE ? OR plate_number LIKE ?) "
        "ORDER BY created_at DESC",
        (q, q, q)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Payment Operations ─────────────────────────────────────────────

def add_payment(client_id, amount, month_covered):
    """Record a monthly payment."""
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (client_id, amount, payment_date, month_covered) VALUES (?, ?, ?, ?)",
        (client_id, amount, date.today().isoformat(), month_covered)
    )
    conn.commit()
    conn.close()


def check_payment_status(client_id, month=None):
    """Check if a client has paid for the given month (default: current month)."""
    if month is None:
        month = date.today().strftime("%Y-%m")
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM payments WHERE client_id = ? AND month_covered = ?",
        (client_id, month)
    ).fetchone()
    conn.close()
    return row is not None


def get_all_payments(client_id=None):
    """Get payment records, optionally filtered by client."""
    conn = get_db()
    if client_id:
        rows = conn.execute(
            "SELECT p.*, c.first_name, c.last_name, c.plate_number "
            "FROM payments p JOIN clients c ON p.client_id = c.id "
            "WHERE p.client_id = ? ORDER BY p.created_at DESC", (client_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT p.*, c.first_name, c.last_name, c.plate_number "
            "FROM payments p JOIN clients c ON p.client_id = c.id "
            "ORDER BY p.created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_payment(payment_id):
    """Delete a payment record."""
    conn = get_db()
    conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()


# ── Access Log Operations ──────────────────────────────────────────

def log_access(plate_number, client_id, client_name, status, gate_action):
    """Log a gate access event."""
    conn = get_db()
    conn.execute(
        "INSERT INTO access_logs (plate_number, client_id, client_name, status, gate_action) "
        "VALUES (?, ?, ?, ?, ?)",
        (plate_number, client_id, client_name or "Unknown", status, gate_action)
    )
    conn.commit()
    conn.close()


def get_access_logs(limit=100):
    """Get recent access log entries."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Statistics ─────────────────────────────────────────────────────

def get_stats():
    """Get dashboard statistics."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM clients WHERE active = 1").fetchone()[0]
    current_month = date.today().strftime("%Y-%m")
    paid = conn.execute(
        "SELECT COUNT(DISTINCT client_id) FROM payments WHERE month_covered = ?",
        (current_month,)
    ).fetchone()[0]
    today_str = date.today().isoformat()
    entries = conn.execute(
        "SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) = ? AND gate_action = 'OPEN'",
        (today_str,)
    ).fetchone()[0]
    denied = conn.execute(
        "SELECT COUNT(*) FROM access_logs WHERE DATE(timestamp) = ? AND gate_action = 'DENIED'",
        (today_str,)
    ).fetchone()[0]
    conn.close()
    return {
        "total_clients": total,
        "paid_this_month": paid,
        "unpaid_this_month": max(0, total - paid),
        "today_entries": entries,
        "today_denied": denied,
    }
