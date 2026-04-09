import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.LeaseService import LeaseService
from source.app.services.InvoiceService import InvoiceService

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

def CountRows(TableName: str, WhereClause: str = "", Params: tuple = ()):
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Sql = f"SELECT COUNT(*) FROM {TableName} {WhereClause}"
    Cursor.execute(Sql, Params)
    Count = Cursor.fetchone()[0]
    Connection.close()
    return Count

def GetInvoiceStatus(InvoiceId: int):
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("SELECT status FROM Invoice WHERE invoice_id = ?", (InvoiceId,))
    Result = Cursor.fetchone()
    Connection.close()
    return Result[0] if Result else None

def Execute():
    print("Running InvoiceService testing...")

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

    LeaseId = LeaseService.CreateLeaseWithInitialInvoice(
        TenantId,
        ApartmentId,
        "2026-02-01",
        "2027-02-01",
        1000.0,
        1200.0,
        "2026-03-01"
    )

    print("All set up.")
    print(f"TenantId={TenantId}, ApartmentId={ApartmentId}, LeaseId={LeaseId}")
    print()
    
    try:
        InvoiceId = InvoiceService.CreateInvoice(
            LeaseId,
            "2026-04-01",
            1200.0
        )

        InvoiceData = InvoiceService.GetInvoiceById(InvoiceId)

        if InvoiceData and InvoiceData[4] == "PENDING":
            print(f"Pass. Valid invoice created with Invoice ID: {InvoiceId}")
        else:
            print("Fail. Invoice was created but status/data was incorrect.")

    except Exception as FailError:
        print(f"Fail. Valid invoice creation raised error: {FailError}")

    try:
        InvoiceService.CreateInvoice(
            999999,
            "2026-05-01",
            1200.0
        )
        print("Fail. Should fail due to invalid lease ID.")

    except Exception as FailError:
        print(f"Pass. Invalid lease ID failed correctly: {FailError}")

    try:
        InvoiceService.MarkInvoicePaid(InvoiceId)
        Status = GetInvoiceStatus(InvoiceId)

        if Status == "PAID":
            print("Pass. Invoice marked as paid correctly.")
        else:
            print(f"Fail. Invoice status should be PAID, got {Status} instead.")

    except Exception as FailError:
        print(f"Fail. Marking invoice paid raised error: {FailError}")

    try:
        OverdueInvoiceId = InvoiceService.CreateInvoice(
            LeaseId,
            "2026-05-01",
            1200.0
        )

        InvoiceService.MarkInvoiceOverdue(OverdueInvoiceId)
        Status = GetInvoiceStatus(OverdueInvoiceId)

        if Status == "OVERDUE":
            print("Pass. Invoice marked as overdue correctly.")
        else:
            print(f"Fail. Invoice status should be OVERDUE, got {Status} instead.")

    except Exception as FailError:
        print(f"Fail. Marking invoice overdue raised error: {FailError}")

    try:
        OverdueInvoices = InvoiceService.GetOverdueInvoices()

        if len(OverdueInvoices) > 0:
            print(f"Pass. Retrieved overdue invoices correctly. Count: {len(OverdueInvoices)}")
        else:
            print("Fail. Expected at least one overdue invoice.")

    except Exception as FailError:
        print(f"Fail. Retrieving overdue invoices raised error: {FailError}")

if __name__ == "__main__":
    Execute()
