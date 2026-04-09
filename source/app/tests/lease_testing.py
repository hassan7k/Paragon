import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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

    Cursor.execute("SELECT apartment_id FROM Apartment WHERE location_id = ? AND apartment_number = ?", (LocationId, "A101"))
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
    print("Lease service testing...")

    ResetDatabase()
    Create_Tables()

    ApartmentId = CreateTempSeed()

    TenantId = TenantService.AddTenant(
        "CB987654A",
        "Jimmy",
        "Smith",
        "07123456789",
        "jimmy.smith@example.co.uk",
        "Student",
        "Ref: Jane Smith"
    )

    print("Client added. Details are :: ")
    print(f"TenantId={TenantId}, ApartmentId={ApartmentId}")
    print()

    try:
        LeaseId = LeaseService.CreateLeaseWithInitialInvoice(
            TenantId,
            ApartmentId,
            "2026-02-01",
            "2027-02-01",
            1000.0,
            1200.0,
            "2026-03-01"
        )

        LeaseCount = CountRows("Lease", "WHERE lease_id = ?", (LeaseId,))
        InvoiceCount = CountRows("Invoice", "WHERE lease_id = ?", (LeaseId,))
        AptStatus = GetApartmentStatus(ApartmentId)

        if LeaseCount == 1 and InvoiceCount == 1 and AptStatus == "OCCUPIED":
            print(f"Lease created (lease_id={LeaseId}), invoice created, apartment occupied.")
        else:
            print("Success path did not create expected rows/status.")
            print("LeaseCount:", LeaseCount, "InvoiceCount:", InvoiceCount, "AptStatus:", AptStatus)

    except Exception as FailError:
        print("Success path raised error:", FailError)


    try:
        CorruptedTenantId = 555555
        LeaseId = LeaseService.CreateLeaseWithInitialInvoice(
            CorruptedTenantId,
            ApartmentId,
            "2026-02-01",
            "2027-02-01",
            1000.0,
            1200.0,
            "2026-03-01"
        )

        print("Test should have failed.")

    except Exception as FailError:
        TotalLeases = CountRows("Lease")
        TotalInvoices = CountRows("Invoice")
        AptStatus = GetApartmentStatus(ApartmentId)

        if TotalLeases == 1 and TotalInvoices == 1:
            print("Pass, no partial lease/invoice created.")
        else:
            print("TotalLeases:", TotalLeases, "TotalInvoices:", TotalInvoices)

        print("Expected failure:", FailError)
        print("Apartment status now:", AptStatus)

if __name__ == "__main__":
    Execute()
