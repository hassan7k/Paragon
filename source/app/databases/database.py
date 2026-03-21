import os
import sqlite3 # Imported database library

# This is the absolute + full path to this file
CurrentDir = os.path.dirname(os.path.abspath(__file__))
DatabasePath = os.path.join(CurrentDir, "paragondata.db")

# A function that connects to the database
def Get_Connection():
    Connection = sqlite3.connect(DatabasePath)
    Connection.execute("PRAGMA foreign_keys = ON;")
    return Connection

def Create_Tables():
    Connection = Get_Connection()
    Cursor = Connection.cursor()

    # Location table
    Cursor.execute("""
    CREATE TABLE IF NOT EXISTS Location (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL UNIQUE
    );
    """)

    # User table
    Cursor.execute("""
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

    # Tenant table
    Cursor.execute("""
    CREATE TABLE IF NOT EXISTS Tenant (
        tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ni_number TEXT NOT NULL UNIQUE,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        occupation TEXT,
        tenant_references TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Apartments table
    Cursor.execute("""
    CREATE TABLE IF NOT EXISTS Apartment (
        apartment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER NOT NULL,
        apartment_number TEXT NOT NULL,
        type TEXT NOT NULL,
        rooms INTEGER NOT NULL CHECK(rooms > 0),
        monthly_rent REAL NOT NULL CHECK(monthly_rent > 0),
        status TEXT NOT NULL DEFAULT 'AVAILABLE'
            CHECK(status IN ('AVAILABLE','OCCUPIED','MAINTENANCE')),
        FOREIGN KEY (location_id) REFERENCES Location(location_id),
        UNIQUE(location_id, apartment_number)
    );
    """)

    # Lease table
    Cursor.execute("""
    CREATE TABLE IF NOT EXISTS Lease (
        lease_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        apartment_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        deposit_amount REAL NOT NULL CHECK(deposit_amount >= 0),
        agreed_monthly_rent REAL NOT NULL CHECK(agreed_monthly_rent > 0),
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK(status IN ('ACTIVE','TERMINATED','PENDING')),
        FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id),
        FOREIGN KEY (apartment_id) REFERENCES Apartment(apartment_id)
    );
    """)

    # Invoice table
    Cursor.execute("""
    CREATE TABLE IF NOT EXISTS Invoice (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        lease_id INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        amount_due REAL NOT NULL CHECK(amount_due > 0),
        status TEXT NOT NULL DEFAULT 'PENDING'
            CHECK(status IN ('PENDING','PAID','OVERDUE')),
        FOREIGN KEY (lease_id) REFERENCES Lease(lease_id)
    );
    """)

    # Payment table
    Cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payment (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        amount REAL NOT NULL CHECK(amount > 0),
        payment_date TEXT NOT NULL,
        method TEXT,
        FOREIGN KEY (invoice_id) REFERENCES Invoice(invoice_id)
    );
    """)

    # Maintenance table
    Cursor.execute("""
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
        time_taken_hours REAL CHECK(time_taken_hours >= 0),
        reported_date TEXT DEFAULT CURRENT_TIMESTAMP,
        resolved_date TEXT,
        cost REAL CHECK(cost >= 0),
        FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id),
        FOREIGN KEY (apartment_id) REFERENCES Apartment(apartment_id)
    );
    """)

    # Complaints table
    Cursor.execute("""
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

    # Indexing 
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_location ON Users(location_id);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_apartment_location ON Apartment(location_id);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_lease_tenant ON Lease(tenant_id);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_lease_apartment ON Lease(apartment_id);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_lease ON Invoice(lease_id);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_invoice ON Payment(invoice_id);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_apartment ON MaintenanceRequest(apartment_id);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_status ON MaintenanceRequest(status);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_priority ON MaintenanceRequest(priority);")
    Cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_tenant ON MaintenanceRequest(tenant_id);")

    Connection.commit()
    Connection.close()