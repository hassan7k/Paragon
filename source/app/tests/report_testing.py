import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.LeaseService import LeaseService
from source.app.services.InvoiceService import InvoiceService
from source.app.services.PaymentService import PaymentService
from source.app.services.MaintenanceService import MaintenanceService
from source.app.services.ComplaintService import ComplaintService
from source.app.services.ReportingService import ReportingService

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
        INSERT INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
        VALUES (?, ?, ?, ?, ?, 'AVAILABLE')
    """, (LocationId, "A102", "FLAT", 3, 1500.0))

    Cursor.execute("""
        SELECT apartment_id
        FROM Apartment
        WHERE apartment_number = 'A101'
    """)
    ApartmentId = Cursor.fetchone()[0]

    Connection.commit()
    Connection.close()

    return ApartmentId

def Execute():
    print("Running ReportingService testing...")

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
        "Ref"
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

    PaymentService.RecordPayment(
        InvoiceId,
        1200.0,
        "CARD"
    )

    OverdueInvoiceId = InvoiceService.CreateInvoice(
        LeaseId,
        "2026-05-01",
        1200.0
    )
    InvoiceService.MarkInvoiceOverdue(OverdueInvoiceId)

    MaintenanceService.CreateMaintenanceRequest(
        TenantId,
        ApartmentId,
        "Leaking pipe in bathroom",
        "HIGH"
    )
    MaintenanceService.ResolveMaintenanceRequest(1, 250.0)

    ComplaintService.CreateComplaint(
        TenantId,
        "Noise complaint"
    )

    print("All set up.")
    print()

    try:
        Occupancy = ReportingService.GetOccupancyByLocation()
        if len(Occupancy) >= 1:
            print(f"Pass. Occupancy report retrieved correctly. Rows: {len(Occupancy)}")
        else:
            print("Fail. Occupancy report returned no rows.")
    except Exception as FailError:
        print(f"Fail. Occupancy report raised error: {FailError}")

    try:
        FinanceSummary = ReportingService.GetCollectedVsPendingRent()
        if FinanceSummary:
            print(f"Pass. Financial summary retrieved correctly: {FinanceSummary}")
        else:
            print("Fail. Financial summary returned no data.")
    except Exception as FailError:
        print(f"Fail. Financial summary raised error: {FailError}")

    try:
        OverdueInvoices = ReportingService.GetOverdueInvoices()
        if len(OverdueInvoices) >= 1:
            print(f"Pass. Overdue invoices retrieved correctly. Count: {len(OverdueInvoices)}")
        else:
            print("Fail. Expected at least one overdue invoice.")
    except Exception as FailError:
        print(f"Fail. Overdue invoice report raised error: {FailError}")

    try:
        MaintenanceSummary = ReportingService.GetMaintenanceCostSummary()
        if MaintenanceSummary:
            print(f"Pass. Maintenance summary retrieved correctly: {MaintenanceSummary}")
        else:
            print("Fail. Maintenance summary returned no data.")
    except Exception as FailError:
        print(f"Fail. Maintenance summary raised error: {FailError}")

    try:
        ComplaintSummary = ReportingService.GetComplaintsSummary()
        if len(ComplaintSummary) >= 1:
            print(f"Pass. Complaint summary retrieved correctly. Rows: {len(ComplaintSummary)}")
        else:
            print("Fail. Complaint summary returned no rows.")
    except Exception as FailError:
        print(f"Fail. Complaint summary raised error: {FailError}")

    try:
        TenantPayments = ReportingService.GetTenantPaymentHistory(TenantId)
        if len(TenantPayments) >= 1:
            print(f"Pass. Tenant payments report retrieved correctly. Count: {len(TenantPayments)}")
        else:
            print("Fail. Expected at least one payment for tenant.")
    except Exception as FailError:
        print(f"Fail. Tenant payment report raised error: {FailError}")

if __name__ == "__main__":
    Execute()
