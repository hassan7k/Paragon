import os
from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.ComplaintService import ComplaintService

def ResetDatabase():
    if os.path.exists(DatabasePath):
        os.remove(DatabasePath)

def CreateTempSeed():
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("INSERT INTO Location (city) VALUES (?)", ("Bristol",))
    Cursor.execute("SELECT location_id FROM Location WHERE city = ?", ("Bristol",))
    LocationId = Cursor.fetchone()[0]
    Cursor.execute("""
        INSERT INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
        VALUES (?, ?, ?, ?, ?, 'AVAILABLE')
    """, (LocationId, "A101", "FLAT", 2, 1200.0))
    Connection.commit()
    Connection.close()
    return LocationId

def Execute():
    print("Running ComplaintService testing...")

    ResetDatabase()
    Create_Tables()
    LocationId = CreateTempSeed()

    TenantId = TenantService.AddTenant(
        "CB987654A", "Jimmy", "Smith", "07123456789",
        "jimmy.smith@example.co.uk", "Student", "Ref: Jane"
    )

    print(f"Seed done. TenantId={TenantId}")
    print()

    # Test 1: Create complaint
    try:
        CompId = ComplaintService.CreateComplaint(TenantId, "Noisy neighbours at night")
        print(f"Pass. Complaint created with ID: {CompId}")
    except Exception as FailError:
        print(f"Fail. Complaint creation raised error: {FailError}")

    # Test 2: Empty description
    try:
        ComplaintService.CreateComplaint(TenantId, "")
        print("Fail. Should fail due to empty description.")
    except Exception as FailError:
        print(f"Pass. Empty description failed correctly: {FailError}")

    # Test 3: Get complaint by ID
    try:
        Comp = ComplaintService.GetComplaintById(CompId)
        if Comp and Comp[3] == "OPEN":
            print("Pass. GetComplaintById returned correct data.")
        else:
            print("Fail. Complaint data incorrect.")
    except Exception as FailError:
        print(f"Fail. GetComplaintById raised error: {FailError}")

    # Test 4: Close complaint
    try:
        ComplaintService.CloseComplaint(CompId)
        Comp = ComplaintService.GetComplaintById(CompId)
        if Comp[3] == "CLOSED":
            print("Pass. Complaint closed successfully.")
        else:
            print(f"Fail. Status is {Comp[3]}.")
    except Exception as FailError:
        print(f"Fail. CloseComplaint raised error: {FailError}")

if __name__ == "__main__":
    Execute()
