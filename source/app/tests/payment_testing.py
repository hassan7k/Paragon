import os
from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.LeaseService import LeaseService
from source.app.services.InvoiceService import InvoiceService
from source.app.services.PaymentService import PaymentService

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
    print("Running PaymentService testing...")

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

    # Get the auto-created invoice
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("SELECT invoice_id, amount_due FROM Invoice WHERE lease_id = ?", (LeaseId,))
    InvoiceId, AmountDue = Cursor.fetchone()
    Connection.close()

    print(f"Seed done. InvoiceId={InvoiceId}, AmountDue={AmountDue}")
    print()

    # Test 1: Valid payment (exact match)
    try:
        PaymentId = PaymentService.RecordPayment(InvoiceId, AmountDue, "BANK_TRANSFER")
        print(f"Pass. Payment recorded with ID: {PaymentId}")
    except Exception as FailError:
        print(f"Fail. Valid payment raised error: {FailError}")

    # Test 2: Already paid invoice
    try:
        PaymentService.RecordPayment(InvoiceId, AmountDue, "CASH")
        print("Fail. Should fail because invoice already paid.")
    except Exception as FailError:
        print(f"Pass. Already paid failed correctly: {FailError}")

    # Test 3: Amount mismatch
    InvoiceId2 = InvoiceService.CreateInvoice(LeaseId, "2026-04-01", 1200.0)
    try:
        PaymentService.RecordPayment(InvoiceId2, 500.0, "CASH")
        print("Fail. Should fail due to amount mismatch.")
    except Exception as FailError:
        print(f"Pass. Amount mismatch failed correctly: {FailError}")

    # Test 4: Get payments by invoice
    try:
        Payments = PaymentService.GetPaymentsByInvoice(InvoiceId)
        if len(Payments) == 1:
            print("Pass. GetPaymentsByInvoice returned 1 payment.")
        else:
            print(f"Fail. Expected 1 payment, got {len(Payments)}.")
    except Exception as FailError:
        print(f"Fail. GetPaymentsByInvoice raised error: {FailError}")

if __name__ == "__main__":
    Execute()
