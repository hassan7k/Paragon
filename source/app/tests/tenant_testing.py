import os
from source.app.databases.database import Get_Connection, Create_Tables, DatabasePath
from source.app.services.TenantService import TenantService

def ResetDatabase():
    if os.path.exists(DatabasePath):
        os.remove(DatabasePath)

def CreateTempSeed():
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("INSERT OR IGNORE INTO Location (city) VALUES (?)", ("Bristol",))
    Cursor.execute("SELECT location_id FROM Location WHERE city = ?", ("Bristol",))
    LocationId = Cursor.fetchone()[0]
    Cursor.execute("""
        INSERT OR IGNORE INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
        VALUES (?, ?, ?, ?, ?, 'AVAILABLE')
    """, (LocationId, "A101", "FLAT", 2, 1200.0))
    Connection.commit()
    Connection.close()

def Execute():
    print("Running TenantService testing...")

    ResetDatabase()
    Create_Tables()
    CreateTempSeed()
    print("All set up.")
    print()

    # Test 1: Valid tenant
    try:
        TenantId = TenantService.AddTenant(
            "AY123456C", "John", "Doe", "07123456789",
            "john.doe@example.co.uk", "Student", "Landlord ref: Jane Smith"
        )
        print(f"Pass. Valid tenant insert with Tenant ID: {TenantId}")
    except Exception as FailError:
        print(f"Fail. Valid tenant insert raised error: {FailError}")

    # Test 2: Duplicate NI
    try:
        TenantService.AddTenant(
            "AY123456C", "John", "Doe", "07123456789",
            "john.doe@example.co.uk", "Student", "Landlord ref: Jane Smith"
        )
        print("Fail. Should fail due to replicated NI.")
    except Exception as FailError:
        print(f"Pass. Correctly failed due to NI repeated: {FailError}")

    # Test 3: Invalid phone number
    try:
        TenantService.AddTenant(
            "JA123456A", "Jane", "Smith", "7123456789",
            "janesmith@example.co.uk", "Student", "Landlord ref: John Doe"
        )
        print("Fail. Should fail due to invalid phone number.")
    except Exception as FailError:
        print(f"Pass. Invalid phone number failed: {FailError}")

    # Test 4: Invalid email
    try:
        TenantService.AddTenant(
            "WA123456B", "Adam", "Smith", "07123456789",
            "adamexample.co.uk", "Student", "Landlord ref: Jane Smith"
        )
        print("Fail. Should fail due to invalid email address.")
    except Exception as FailError:
        print(f"Pass. Invalid email address failed: {FailError}")

if __name__ == "__main__":
    Execute()
