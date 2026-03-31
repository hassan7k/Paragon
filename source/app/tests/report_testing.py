import os
from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.TenantService import TenantService
from source.app.services.LeaseService import LeaseService
from source.app.services.PaymentService import PaymentService
from source.app.services.InvoiceService import InvoiceService
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
    Cursor.execute("INSERT INTO Location (city) VALUES (?)", ("Cardiff",))
    Cursor.execute("SELECT location_id FROM Location WHERE city = 'Bristol'")
    BristolId = Cursor.fetchone()[0]
    Cursor.execute("SELECT location_id FROM Location WHERE city = 'Cardiff'")
    CardiffId = Cursor.fetchone()[0]

    Cursor.execute("""
        INSERT INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
        VALUES (?, ?, ?, ?, ?, 'AVAILABLE')
    """, (BristolId, "A101", "FLAT", 2, 1200.0))
    Cursor.execute("""
        INSERT INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
        VALUES (?, ?, ?, ?, ?, 'AVAILABLE')
    """, (CardiffId, "C101", "FLAT", 3, 1400.0))

    Connection.commit()
    Connection.close()
    return BristolId, CardiffId

def Execute():
    print("Running ReportingService testing...")

    ResetDatabase()
    Create_Tables()
    BristolId, CardiffId = CreateTempSeed()

    # Create tenant, lease, invoice, payment
    TenantId = TenantService.AddTenant(
        "CB987654A", "Jimmy", "Smith", "07123456789",
        "jimmy.smith@example.co.uk", "Student", "Ref: Jane"
    )

    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("SELECT apartment_id FROM Apartment WHERE apartment_number = 'A101'")
    AptId = Cursor.fetchone()[0]
    Connection.close()

    LeaseId = LeaseService.CreateLeaseWithInitialInvoice(
        TenantId, AptId, "2026-02-01", "2027-02-01",
        1000.0, 1200.0, "2026-03-01"
    )

    # Get invoice and pay it
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("SELECT invoice_id, amount_due FROM Invoice WHERE lease_id = ?", (LeaseId,))
    InvId, Amount = Cursor.fetchone()
    Connection.close()
    PaymentService.RecordPayment(InvId, Amount, "BANK_TRANSFER")

    # Create maintenance request and resolve it
    MaintenanceService.CreateMaintenanceRequest(TenantId, AptId, "Broken tap", "MEDIUM")
    Connection = Get_Connection()
    Cursor = Connection.cursor()
    Cursor.execute("SELECT request_id FROM MaintenanceRequest LIMIT 1")
    ReqId = Cursor.fetchone()[0]
    Connection.close()
    MaintenanceService.ResolveMaintenanceRequest(ReqId, 150.0)

    # Create complaint
    ComplaintService.CreateComplaint(TenantId, "Parking issues")

    print("Seed data created.")
    print()

    # Test 1: Occupancy summary
    try:
        Result = ReportingService.GetOccupancySummary()
        if Result[0] == 2:
            print(f"Pass. Occupancy summary: total={Result[0]}, occupied={Result[1]}, available={Result[2]}")
        else:
            print(f"Fail. Expected 2 total apartments, got {Result[0]}")
    except Exception as FailError:
        print(f"Fail. GetOccupancySummary raised error: {FailError}")

    # Test 2: Collected vs pending rent
    try:
        Result = ReportingService.GetCollectedVsPendingRent()
        if Result[0] > 0:
            print(f"Pass. Collected: {Result[0]}, Pending: {Result[1]}")
        else:
            print(f"Fail. Expected collected > 0, got {Result[0]}")
    except Exception as FailError:
        print(f"Fail. GetCollectedVsPendingRent raised error: {FailError}")

    # Test 3: Maintenance cost summary
    try:
        Result = ReportingService.GetMaintenanceCostSummary()
        if Result[0] == 1 and Result[1] == 150.0:
            print(f"Pass. Maintenance: {Result[0]} resolved, cost={Result[1]}")
        else:
            print(f"Fail. Expected 1 resolved / 150.0, got {Result}")
    except Exception as FailError:
        print(f"Fail. GetMaintenanceCostSummary raised error: {FailError}")

    # Test 4: Occupancy by location
    try:
        Result = ReportingService.GetOccupancyByLocation()
        if len(Result) == 2:
            print(f"Pass. Occupancy by location returned {len(Result)} locations.")
        else:
            print(f"Fail. Expected 2 locations, got {len(Result)}")
    except Exception as FailError:
        print(f"Fail. GetOccupancyByLocation raised error: {FailError}")

if __name__ == "__main__":
    Execute()
