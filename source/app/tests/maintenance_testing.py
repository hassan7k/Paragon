import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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

    Cursor.execute("""
        SELECT apartment_id
        FROM Apartment
        WHERE location_id = ? AND apartment_number = ?
    """, (LocationId, "A101"))
    ApartmentId = Cursor.fetchone()[0]

    Connection.commit()
    Connection.close()

    return ApartmentId

def Execute():
    print("Running MaintenanceService testing...")

    ResetDatabase()
    Create_Tables()
    ApartmentId = CreateTempSeed()

    TenantId = TenantService.AddTenant(
        "AY123456C",
        "John",
        "Doe",
        "07123456789",
        "john.doe@example.co.uk",
        "Student",
        "Ref: Jane Smith"
    )

    print("All set up.")
    print(f"TenantId={TenantId}, ApartmentId={ApartmentId}")
    print()

    RequestId = None

    try:
        RequestId = MaintenanceService.CreateMaintenanceRequest(
            TenantId,
            ApartmentId,
            "Leaking pipe in kitchen",
            "HIGH"
        )
        print(f"Pass. Maintenance request created with Request ID: {RequestId}")

    except Exception as FailError:
        print(f"Fail. Valid maintenance request raised error: {FailError}")

    try:
        MaintenanceService.CreateMaintenanceRequest(
            999999,
            999999,
            "Broken heater",
            "MEDIUM"
        )
        print("Fail. Should fail due to invalid tenant/apartment.")

    except Exception as FailError:
        print(f"Pass. Invalid tenant/apartment failed correctly: {FailError}")

    try:
        MaintenanceService.CreateMaintenanceRequest(
            TenantId,
            ApartmentId,
            "Broken window",
            "URGENT"
        )
        print("Fail. Should fail due to invalid priority.")

    except Exception as FailError:
        print(f"Pass. Invalid priority failed correctly: {FailError}")

    try:
        if RequestId is not None:
            MaintenanceService.UpdateMaintenanceStatus(RequestId, "IN_PROGRESS")
            RequestData = MaintenanceService.GetRequestById(RequestId)

            if RequestData and RequestData[5] == "IN_PROGRESS":
                print("Pass. Maintenance status updated correctly.")
            else:
                print(f"Fail. Status should be IN_PROGRESS, got {RequestData[5]} instead.")
        else:
            print("Skipped. Status update test could not run.")

    except Exception as FailError:
        print(f"Fail. Updating maintenance status raised error: {FailError}")

    try:
        if RequestId is not None:
            MaintenanceService.ResolveMaintenanceRequest(RequestId, 250.0)
            RequestData = MaintenanceService.GetRequestById(RequestId)

            if RequestData and RequestData[5] == "RESOLVED" and RequestData[8] == 250.0:
                print("Pass. Maintenance request resolved correctly.")
            else:
                print("Fail. Maintenance resolution data is incorrect.")
        else:
            print("Skipped. Resolve request test could not run.")

    except Exception as FailError:
        print(f"Fail. Resolving maintenance request raised error: {FailError}")

    try:
        Requests = MaintenanceService.GetRequestsByApartment(ApartmentId)

        if len(Requests) >= 1:
            print(f"Pass. Requests retrieved by apartment correctly. Count: {len(Requests)}")
        else:
            print("Fail. Expected at least one request for this apartment.")

    except Exception as FailError:
        print(f"Fail. Retrieving requests by apartment raised error: {FailError}")

    try:
        Requests = MaintenanceService.GetRequestsByTenant(TenantId)

        if len(Requests) >= 1:
            print(f"Pass. Requests retrieved by tenant correctly. Count: {len(Requests)}")
        else:
            print("Fail. Expected at least one request for this tenant.")

    except Exception as FailError:
        print(f"Fail. Retrieving requests by tenant raised error: {FailError}")

if __name__ == "__main__":
    Execute()
