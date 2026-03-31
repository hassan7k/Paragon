import os
from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.LeaseService import LeaseService

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
    return ApartmentId

def CountRows(TableName: str, Clause: str = "", Params: tuple = ()):
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Sql = f"SELECT COUNT(*) FROM {TableName} {Clause}"
    Cursor.execute(Sql, Params)
    Count = Cursor.fetchone()[0]
    Connection.close()
    return Count

def GetApartmentStatus(ApartmentId: int) -> str:
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("SELECT status FROM Apartment WHERE apartment_id = ?", (ApartmentId,))
    Status = Cursor.fetchone()[0]
    Connection.close()
    return Status

def Execute():
    print("Running LeaseService testing...")

    ResetDatabase()
    Create_Tables()
    ApartmentId = CreateTempSeed()

    TenantId = TenantService.AddTenant(
        "CB987654A", "Jimmy", "Smith", "07123456789",
        "jimmy.smith@example.co.uk", "Student", "Ref: Jane Smith"
    )

    print("Client added. Details are:")
    print(f"TenantId={TenantId}, ApartmentId={ApartmentId}")
    print()

    # Test 1: Valid lease creation (end date in the past so standard termination can be tested)
    try:
        LeaseId = LeaseService.CreateLeaseWithInitialInvoice(
            TenantId, ApartmentId,
            "2024-01-01", "2025-01-01",
            1000.0, 1200.0, "2024-02-01"
        )
        LeaseCount = CountRows("Lease", "WHERE lease_id = ?", (LeaseId,))
        InvoiceCount = CountRows("Invoice", "WHERE lease_id = ?", (LeaseId,))
        AptStatus = GetApartmentStatus(ApartmentId)

        if LeaseCount == 1 and InvoiceCount == 1 and AptStatus == "OCCUPIED":
            print(f"Pass. Lease created (lease_id={LeaseId}), invoice created, apartment occupied.")
        else:
            print("Fail. Expected rows/status not met.")
    except Exception as FailError:
        print(f"Fail. Success path raised error: {FailError}")

    # Test 2: Invalid tenant ID (foreign key failure)
    try:
        LeaseService.CreateLeaseWithInitialInvoice(
            555555, ApartmentId,
            "2024-01-01", "2025-01-01",
            1000.0, 1200.0, "2024-02-01"
        )
        print("Fail. Should have failed with invalid tenant.")
    except Exception as FailError:
        TotalLeases = CountRows("Lease")
        TotalInvoices = CountRows("Invoice")
        if TotalLeases == 1 and TotalInvoices == 1:
            print("Pass. No partial lease/invoice created.")
        else:
            print(f"Fail. TotalLeases: {TotalLeases}, TotalInvoices: {TotalInvoices}")
        print(f"Expected failure: {FailError}")

    # Test 3: Lease termination
    try:
        LeaseService.TerminateLease(LeaseId)
        AptStatus = GetApartmentStatus(ApartmentId)
        if AptStatus == "AVAILABLE":
            print("Pass. Lease terminated, apartment back to AVAILABLE.")
        else:
            print(f"Fail. Apartment status is {AptStatus}, expected AVAILABLE.")
    except Exception as FailError:
        print(f"Fail. Termination raised error: {FailError}")

if __name__ == "__main__":
    Execute()
