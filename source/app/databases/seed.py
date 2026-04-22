from source.app.databases.database import Get_Connection, Create_Tables
from source.app.services.AuthService import AuthService


def _get_location_id(cursor, city: str) -> int:
    cursor.execute("SELECT location_id FROM Location WHERE city = ?", (city,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Location not found: {city}")
    return row[0]


def _safe_create_user(username, password, role, location_id):
    try:
        AuthService.CreateUser(username, password, role, location_id)
    except ValueError:
        pass


def Seed_Test_Data():
    Create_Tables()

    connection = Get_Connection()
    cursor = connection.cursor()

    # Locations
    cursor.execute("INSERT OR IGNORE INTO Location (city) VALUES (?)", ("London",))
    cursor.execute("INSERT OR IGNORE INTO Location (city) VALUES (?)", ("Bristol",))
    connection.commit()

    london_id = _get_location_id(cursor, "London")
    bristol_id = _get_location_id(cursor, "Bristol")

    # Tenants
    cursor.execute("""
        INSERT OR IGNORE INTO Tenant (
            ni_number, first_name, last_name, phone, email, occupation, tenant_references
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "AB123456C", "John", "Smith", "07123456789",
        "john.smith@email.com", "Engineer", "Reference 1"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO Tenant (
            ni_number, first_name, last_name, phone, email, occupation, tenant_references
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "CD789012E", "Sarah", "Jones", "07987654321",
        "sarah.jones@email.com", "Teacher", "Reference 2"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO Tenant (
            ni_number, first_name, last_name, phone, email, occupation, tenant_references
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "EF345678A", "Michael", "Brown", "07000111222",
        "michael.brown@email.com", "Developer", "Reference 3"
    ))

    # Apartments
    cursor.execute("""
        INSERT OR IGNORE INTO Apartment (
            location_id, apartment_number, type, rooms, monthly_rent, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        london_id, "L101", "2 Bedroom", 2, 1200.00, "OCCUPIED"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO Apartment (
            location_id, apartment_number, type, rooms, monthly_rent, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        bristol_id, "B202", "1 Bedroom", 1, 900.00, "OCCUPIED"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO Apartment (
            location_id, apartment_number, type, rooms, monthly_rent, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        london_id, "L102", "Studio", 1, 800.00, "AVAILABLE"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO Apartment (
            location_id, apartment_number, type, rooms, monthly_rent, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        bristol_id, "B203", "Studio", 1, 850.00, "AVAILABLE"
    ))

    connection.commit()

    cursor.execute("SELECT tenant_id, first_name, last_name, ni_number FROM Tenant")
    print("Tenants:", cursor.fetchall())

    cursor.execute("SELECT apartment_id, apartment_number, type, location_id, status FROM Apartment")
    print("Apartments:", cursor.fetchall())
    connection.close()

    # Clearer demo accounts by role + scope
    _safe_create_user("maint_london", "pass123", "MAINTENANCE", london_id)
    _safe_create_user("maint_bristol", "pass123", "MAINTENANCE", bristol_id)

    _safe_create_user("finance_london", "pass123", "FINANCE", london_id)
    _safe_create_user("finance_bristol", "pass123", "FINANCE", bristol_id)

    _safe_create_user("frontdesk_london", "pass123", "FRONT_DESK", london_id)
    _safe_create_user("frontdesk_bristol", "pass123", "FRONT_DESK", bristol_id)

    _safe_create_user("admin_london", "pass123", "ADMIN", london_id)
    _safe_create_user("admin_bristol", "pass123", "ADMIN", bristol_id)

    _safe_create_user("manager_global", "manager123", "MANAGER", london_id)

    print("Test data inserted successfully.")
    print("FRONT DESK: frontdesk_london / pass123")
    print("FRONT DESK: frontdesk_bristol / pass123")
    print("ADMIN: admin_london / pass123")
    print("ADMIN: admin_bristol / pass123")
    print("FINANCE: finance_london / pass123")
    print("FINANCE: finance_bristol / pass123")
    print("MAINTENANCE: maint_london / pass123")
    print("MAINTENANCE: maint_bristol / pass123")
    print("MANAGER: manager_global / manager123")


if __name__ == "__main__":
    Seed_Test_Data()
