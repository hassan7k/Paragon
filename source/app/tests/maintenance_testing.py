import os
from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.MaintenanceService import MaintenanceService

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
    Cursor.execute("SELECT apartment_id FROM Apartment WHERE location_id = ? AND apartment_number = ?",
                   (LocationId, "A101"))
    ApartmentId = Cursor.fetchone()[0]
    Connection.commit()
    Connection.close()
    return LocationId, ApartmentId

def Execute():
    print("Running MaintenanceService testing...")

    ResetDatabase()
    Create_Tables()
    LocationId, ApartmentId = CreateTempSeed()

    TenantId = TenantService.AddTenant(
        "CB987654A", "Jimmy", "Smith", "07123456789",
        "jimmy.smith@example.co.uk", "Student", "Ref: Jane"
    )

    print(f"Seed done. TenantId={TenantId}, ApartmentId={ApartmentId}")
    print()

    # Test 1: Create maintenance request
    try:
        ReqId = MaintenanceService.CreateMaintenanceRequest(
            TenantId, ApartmentId, "Broken window in bedroom", "HIGH"
        )
        print(f"Pass. Maintenance request created with ID: {ReqId}")
    except Exception as FailError:
        print(f"Fail. Request creation raised error: {FailError}")

    # Test 2: Invalid priority
    try:
        MaintenanceService.CreateMaintenanceRequest(
            TenantId, ApartmentId, "Leaky tap", "CRITICAL"
        )
        print("Fail. Should fail due to invalid priority.")
    except Exception as FailError:
        print(f"Pass. Invalid priority failed correctly: {FailError}")

    # Test 3: Update status to IN_PROGRESS
    try:
        MaintenanceService.UpdateMaintenanceStatus(ReqId, "IN_PROGRESS")
        Req = MaintenanceService.GetRequestById(ReqId)
        if Req[5] == "IN_PROGRESS":
            print("Pass. Status updated to IN_PROGRESS.")
        else:
            print(f"Fail. Status is {Req[5]}.")
    except Exception as FailError:
        print(f"Fail. Status update raised error: {FailError}")

    # Test 4: Resolve request
    try:
        MaintenanceService.ResolveMaintenanceRequest(ReqId, 250.0)
        Req = MaintenanceService.GetRequestById(ReqId)
        if Req[5] == "RESOLVED" and Req[8] == 250.0:
            print("Pass. Request resolved with cost 250.0.")
        else:
            print(f"Fail. Status={Req[5]}, Cost={Req[8]}")
    except Exception as FailError:
        print(f"Fail. Resolve raised error: {FailError}")

if __name__ == "__main__":
    Execute()
