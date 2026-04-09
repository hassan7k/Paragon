import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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

    Cursor.execute("""
        SELECT apartment_id
        FROM Apartment
        WHERE location_id = ? AND apartment_number = ?
    """, (LocationId, "A101"))
    ApartmentId = Cursor.fetchone()[0]

    Connection.commit()
    Connection.close()

    return ApartmentId

def GetInvoiceStatus(InvoiceId: int):
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("SELECT status FROM Invoice WHERE invoice_id = ?", (InvoiceId,))
    Result = Cursor.fetchone()
    Connection.close()
    return Result[0] if Result else None

def Execute():
    print("Running PaymentService testing...")

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

    InvoiceId = InvoiceService.CreateInvoice(
        LeaseId,
        "2026-04-01",
        1200.0
    )

    print("All set up.")
    print(f"TenantId={TenantId}, ApartmentId={ApartmentId}, LeaseId={LeaseId}, InvoiceId={InvoiceId}")
    print()

    PaymentId = None

    try:
        PaymentId = PaymentService.RecordPayment(
            InvoiceId,
            1200.0,
            "card"
        )

        InvoiceStatus = GetInvoiceStatus(InvoiceId)

        if InvoiceStatus == "PAID":
            print(f"Pass. Valid payment recorded with Payment ID: {PaymentId}")
        else:
            print(f"Fail. Payment recorded but invoice status should be PAID, got {InvoiceStatus} instead.")

    except Exception as FailError:
        print(f"Fail. Valid payment raised error: {FailError}")

    try:
        PaymentService.RecordPayment(
            InvoiceId,
            1200.0,
            "card"
        )
        print("Fail. Should fail because invoice is already paid.")

    except Exception as FailError:
        print(f"Pass. Duplicate payment failed correctly: {FailError}")

    try:
        PaymentService.RecordPayment(
            999999,
            1200.0,
            "card"
        )
        print("Fail. Should fail due to invalid invoice ID.")

    except Exception as FailError:
        print(f"Pass. Invalid invoice ID failed correctly: {FailError}")

    try:
        AnotherInvoiceId = InvoiceService.CreateInvoice(
            LeaseId,
            "2026-05-01",
            1200.0
        )

        PaymentService.RecordPayment(
            AnotherInvoiceId,
            1000.0,
            "card"
        )
        print("Fail. Should fail due to incorrect payment amount.")

    except Exception as FailError:
        print(f"Pass. Incorrect payment amount failed correctly: {FailError}")

    try:
        Payments = PaymentService.GetPaymentsByInvoice(InvoiceId)

        if len(Payments) >= 1:
            print(f"Pass. Payments retrieved by invoice correctly. Count: {len(Payments)}")
        else:
            print("Fail. Expected at least one payment for this invoice.")

    except Exception as FailError:
        print(f"Fail. Retrieving payments by invoice raised error: {FailError}")

    try:
        TenantPayments = PaymentService.GetPaymentsByTenant(TenantId)

        if len(TenantPayments) >= 1:
            print(f"Pass. Payments retrieved by tenant correctly. Count: {len(TenantPayments)}")
        else:
            print("Fail. Expected at least one payment for this tenant.")

    except Exception as FailError:
        print(f"Fail. Retrieving payments by tenant raised error: {FailError}")

if __name__ == "__main__":
    Execute()
