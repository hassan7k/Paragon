from source.app.databases.database import Get_Connection, Create_Tables
from source.app.services.AuthService import AuthService


def Seed_Test_Data():
    Create_Tables()

    Connection = Get_Connection()
    Cursor = Connection.cursor()

    # Insert locations
    Cursor.execute("INSERT OR IGNORE INTO Location (city) VALUES (?)", ("London",))
    Cursor.execute("INSERT OR IGNORE INTO Location (city) VALUES (?)", ("Bristol",))

    # Insert tenants
    Cursor.execute("""
        INSERT OR IGNORE INTO Tenant (
            ni_number, first_name, last_name, phone, email, occupation, tenant_references
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "AB123456C", "John", "Smith", "07123456789",
        "john.smith@email.com", "Engineer", "Reference 1"
    ))

    Cursor.execute("""
        INSERT OR IGNORE INTO Tenant (
            ni_number, first_name, last_name, phone, email, occupation, tenant_references
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "CD789012E", "Sarah", "Jones", "07987654321",
        "sarah.jones@email.com", "Teacher", "Reference 2"
    ))

    # Insert apartments
    Cursor.execute("""
        INSERT OR IGNORE INTO Apartment (
            location_id, apartment_number, type, rooms, monthly_rent, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        1, "A101", "2 Bedroom", 2, 1200.00, "OCCUPIED"
    ))

    Cursor.execute("""
        INSERT OR IGNORE INTO Apartment (
            location_id, apartment_number, type, rooms, monthly_rent, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        2, "B202", "1 Bedroom", 1, 900.00, "OCCUPIED"
    ))

     # Insert new tenant
    Cursor.execute("""
        INSERT OR IGNORE INTO Tenant (
            ni_number, first_name, last_name, phone, email, occupation, tenant_references
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "EF345678A", "Michael", "Brown", "07000111222",
        "michael.brown@email.com", "Developer", "Reference 3"
    ))
 
    # Insert new apartment
    Cursor.execute("""
        INSERT OR IGNORE INTO Apartment (
            location_id, apartment_number, type, rooms, monthly_rent, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        1, "A102", "Studio", 1, 800.00, "OCCUPIED"
    ))

    Connection.commit()

    Cursor.execute("SELECT tenant_id, first_name, last_name, ni_number FROM Tenant")
    print("Tenants:", Cursor.fetchall())

    Cursor.execute("SELECT apartment_id, apartment_number, type, location_id FROM Apartment")
    print("Apartments:", Cursor.fetchall())
    Connection.close()

    # Create test users
    try:
        AuthService.CreateUser("maint1", "pass123", "MAINTENANCE", 1)
    except ValueError:
        pass

    try:
        AuthService.CreateUser("maint2", "pass123", "MAINTENANCE", 2)
    except ValueError:
        pass

    try:
        AuthService.CreateUser("finance1", "pass123", "FINANCE", 1)
    except ValueError:
        pass

    try:
        AuthService.CreateUser("manager1", "manager123", "MANAGER", 1)
    except ValueError:
        pass

    try:
        AuthService.CreateUser("frontdesk1", "pass123", "FRONT_DESK", 1)
    except ValueError:
        pass

    try:
        AuthService.CreateUser("frontdesk2", "pass123", "FRONT_DESK", 2)
    except ValueError:
        pass

    try:
        AuthService.CreateUser("admin1", "pass123", "ADMIN", 1)
    except ValueError as e:
        print(f"Admin seed skipped: {e}")

    try:
        AuthService.CreateUser("admin2", "pass123", "ADMIN", 2)
    except ValueError as e:
        print(f"Admin seed skipped: {e}")

    print("Test data inserted successfully.")
    print("Maintenance login: maint1 / pass123")
    print("Maintenance login: maint2 / pass123")
    print("Finance login: finance1 / pass123")
    print("Manager login: manager1 / manager123")
    print("Admin login: admin1 / pass123")
    print("Admin login: admin2 / pass123")



if __name__ == "__main__":
    Seed_Test_Data()
    