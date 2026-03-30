import os
import sqlite3

# ---------------- PATH (LOCKED & SAFE) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DatabasePath = os.path.join(BASE_DIR, "paragondata.db")


# ---------------- CONNECTION ----------------
def Get_Connection():
    conn = sqlite3.connect(DatabasePath)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ---------------- CREATE TABLES ----------------
def Create_Tables():
    conn = Get_Connection()
    cur = conn.cursor()

    # ---------------- LOCATION ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Location (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL UNIQUE
    );
    """)

    # ---------------- USERS ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN 
            ('FRONT_DESK','FINANCE','MAINTENANCE','ADMIN','MANAGER')),
        location_id INTEGER NOT NULL,
        FOREIGN KEY (location_id) REFERENCES Location(location_id)
    );
    """)

    # ---------------- TENANT ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Tenant (
        tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ni_number TEXT NOT NULL UNIQUE,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        occupation TEXT,
        tenant_references TEXT,
        apartment_requirement TEXT,
        preferred_lease_years INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # ---------------- APARTMENT ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Apartment (
        apartment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER NOT NULL,
        apartment_number TEXT NOT NULL,
        type TEXT NOT NULL,
        rooms INTEGER NOT NULL,
        monthly_rent REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'AVAILABLE'
            CHECK(status IN ('AVAILABLE','OCCUPIED','MAINTENANCE')),
        FOREIGN KEY (location_id) REFERENCES Location(location_id),
        UNIQUE(location_id, apartment_number)
    );
    """)

    # ---------------- LEASE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Lease (
        lease_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        apartment_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        deposit_amount REAL NOT NULL,
        agreed_monthly_rent REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK(status IN ('ACTIVE','TERMINATED','PENDING')),
        FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id),
        FOREIGN KEY (apartment_id) REFERENCES Apartment(apartment_id)
    );
    """)

    # ---------------- INVOICE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Invoice (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        lease_id INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        amount_due REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING'
            CHECK(status IN ('PENDING','PAID','OVERDUE')),
        FOREIGN KEY (lease_id) REFERENCES Lease(lease_id)
    );
    """)

    # ---------------- PAYMENT ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Payment (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        method TEXT,
        FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
    );
    """)

    # ---------------- MAINTENANCE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS MaintenanceRequest (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        apartment_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        priority TEXT NOT NULL CHECK(priority IN ('LOW','MEDIUM','HIGH')),
        status TEXT NOT NULL DEFAULT 'REPORTED'
            CHECK(status IN ('REPORTED','SCHEDULED','IN_PROGRESS','RESOLVED')),
        assigned_worker TEXT,
        scheduled_date TEXT,
        scheduled_time TEXT,
        resolution_notes TEXT,
        time_taken_hours REAL,
        reported_date TEXT DEFAULT CURRENT_TIMESTAMP,
        resolved_date TEXT,
        cost REAL,
        FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id),
        FOREIGN KEY (apartment_id) REFERENCES Apartment(apartment_id)
    );
    """)

    # ---------------- COMPLAINT ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Complaint (
        complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        status TEXT DEFAULT 'OPEN'
            CHECK(status IN ('OPEN','CLOSED')),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id)
    );
    """)

    # ---------------- INDEXES (PERFORMANCE) ----------------
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lease_tenant ON Lease(tenant_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_invoice_lease ON Invoice(lease_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payment_invoice ON Payment(invoice_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_tenant ON MaintenanceRequest(tenant_id);")

    conn.commit()
    conn.close()