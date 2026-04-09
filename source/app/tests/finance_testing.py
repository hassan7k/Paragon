import os
from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.LeaseService import LeaseService
from source.app.services.InvoiceService import InvoiceService
from source.app.services.PaymentService import PaymentService
from source.app.services.MaintenanceService import MaintenanceService
from source.app.services.FinanceService import FinanceService


def ResetDatabase():
    if os.path.exists(DatabasePath):
        os.remove(DatabasePath)


def CreateTempSeed():
    Connection = Get_Connection()
    Cursor = Connection.cursor()

    Cursor.execute("INSERT INTO Location (city) VALUES (?)", ("Bristol",))
    Cursor.execute(
        "SELECT location_id FROM Location WHERE city = ?", ("Bristol",))
    LocationId = Cursor.fetchone()[0]

    Cursor.execute("""
        INSERT INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
        VALUES (?, 'A101', 'FLAT', 2, 1200.0, 'AVAILABLE')
    """, (LocationId,))

    Cursor.execute(
        "SELECT apartment_id FROM Apartment WHERE apartment_number = 'A101'")
    ApartmentId = Cursor.fetchone()[0]

    Connection.commit()
    Connection.close()

    return LocationId, ApartmentId


def Execute():
    print("Running FinanceService testing...")

    ResetDatabase()
    Create_Tables()
    LocationId, ApartmentId = CreateTempSeed()

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
        "Broken heater",
        "HIGH"
    )
    MaintenanceService.ResolveMaintenanceRequest(1, 250.0)

    print("All set up.")
    print()

    # 1. financial summary
    try:
        Summary = FinanceService.GetFinancialSummaryByLocation(LocationId)
        if "total_due" in Summary and "total_collected" in Summary:
            print("Pass. Financial summary retrieved correctly.")
        else:
            print("Fail. Financial summary missing expected fields.")
    except Exception as FailError:
        print(f"Fail. Financial summary raised error: {FailError}")

    # 2. tenant balance
    try:
        Balance = FinanceService.GetTenantBalance(TenantId)
        print(f"Pass. Tenant balance retrieved: {Balance}")
    except Exception as FailError:
        print(f"Fail. Tenant balance raised error: {FailError}")

    # 3. overdue invoices
    try:
        Overdue = FinanceService.GetOverdueInvoices()
        if len(Overdue) >= 1:
            print("Pass. Overdue invoices retrieved correctly.")
        else:
            print("Fail. Expected at least one overdue invoice.")
    except Exception as FailError:
        print(f"Fail. Overdue invoice retrieval raised error: {FailError}")

    # 4. monthly revenue
    try:
        Report = FinanceService.GetMonthlyRevenue(2026, 4)
        if "collected" in Report:
            print("Pass. Monthly revenue report retrieved correctly.")
        else:
            print("Fail. Monthly revenue missing expected fields.")
    except Exception as FailError:
        print(f"Fail. Monthly revenue raised error: {FailError}")

    # 5. maintenance cost
    try:
        Cost = FinanceService.GetMaintenanceCostSummary(LocationId)
        print(f"Pass. Maintenance cost summary retrieved: {Cost}")
    except Exception as FailError:
        print(f"Fail. Maintenance cost raised error: {FailError}")

    # 6. full finance report
    try:
        Full = FinanceService.GenerateFinanceReport(LocationId)
        if "net_revenue" in Full:
            print("Pass. Full finance report retrieved correctly.")
        else:
            print("Fail. Full finance report missing expected fields.")
    except Exception as FailError:
        print(f"Fail. Full finance report raised error: {FailError}")


if __name__ == "__main__":
    Execute()
