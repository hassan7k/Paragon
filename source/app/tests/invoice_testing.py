import os
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
    Cursor.execute("SELECT apartment_id FROM Apartment WHERE location_id = ? AND apartment_number = ?",
                   (LocationId, "A101"))
    ApartmentId = Cursor.fetchone()[0]
    Connection.commit()
    Connection.close()
    return LocationId, ApartmentId

def Execute():
    print("Running InvoiceService testing...")

    ResetDatabase()
    Create_Tables()
    LocationId, ApartmentId = CreateTempSeed()

    TenantId = TenantService.AddTenant(
        "CB987654A", "Jimmy", "Smith", "07123456789",
        "jimmy.smith@example.co.uk", "Student", "Ref: Jane"
    )
    LeaseId = LeaseService.CreateLeaseWithInitialInvoice(
        TenantId, ApartmentId, "2026-02-01", "2027-02-01",
        1000.0, 1200.0, "2026-03-01"
    )
    print(f"Seed done. LeaseId={LeaseId}")
    print()

    # Test 1: Create additional invoice
    try:
        InvoiceId = InvoiceService.CreateInvoice(LeaseId, "2026-04-01", 1200.0)
        print(f"Pass. Invoice created with ID: {InvoiceId}")
    except Exception as FailError:
        print(f"Fail. Invoice creation raised error: {FailError}")

    # Test 2: Get invoices by lease
    try:
        Invoices = InvoiceService.GetInvoiceByLease(LeaseId)
        if len(Invoices) == 2:
            print("Pass. GetInvoiceByLease returned 2 invoices.")
        else:
            print(f"Fail. Expected 2 invoices, got {len(Invoices)}.")
    except Exception as FailError:
        print(f"Fail. GetInvoiceByLease raised error: {FailError}")

    # Test 3: Mark invoice paid
    try:
        InvoiceService.MarkInvoicePaid(InvoiceId)
        Inv = InvoiceService.GetInvoiceById(InvoiceId)
        if Inv[4] == "PAID":
            print("Pass. Invoice marked as PAID.")
        else:
            print(f"Fail. Invoice status is {Inv[4]}.")
    except Exception as FailError:
        print(f"Fail. MarkInvoicePaid raised error: {FailError}")

    # Test 4: Mark invoice overdue
    try:
        Inv2 = InvoiceService.GetInvoiceByLease(LeaseId)[0]
        InvoiceService.MarkInvoiceOverdue(Inv2[0])
        Check = InvoiceService.GetInvoiceById(Inv2[0])
        if Check[4] == "OVERDUE":
            print("Pass. Invoice marked as OVERDUE.")
        else:
            print(f"Fail. Invoice status is {Check[4]}.")
    except Exception as FailError:
        print(f"Fail. MarkInvoiceOverdue raised error: {FailError}")

if __name__ == "__main__":
    Execute()
