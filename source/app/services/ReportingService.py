import sqlite3
from source.app.databases.database import Get_Connection

class ReportingService:

    @staticmethod
    def GetCollectedVsPendingRent():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN status = 'PAID' THEN amount_due ELSE 0 END), 0) AS collected_rent,
                COALESCE(SUM(CASE WHEN status IN ('PENDING', 'OVERDUE') THEN amount_due ELSE 0 END), 0) AS pending_rent
            FROM Invoice
            """)
            return Cursor.fetchone()

        finally:
            Connection.close()

    @staticmethod
    def GetMonthlyRevenue(YearMonth: str):
        if not YearMonth or len(YearMonth) != 7:
            raise ValueError("YearMonth must be in format YYYY-MM.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM Payment
                WHERE strftime('%Y-%m', payment_date) = ?
            """, (YearMonth,))
            return Cursor.fetchone()[0]

        finally:
            Connection.close()

    @staticmethod
    def GetOverdueInvoices():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT i.invoice_id, i.lease_id, i.due_date, i.amount_due, i.status
                FROM Invoice i
                WHERE i.status = 'OVERDUE'
                ORDER BY i.due_date
            """)
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def GetOccupancySummary():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    COUNT(apartment_id) AS total_apartments,
                    SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied_apartments,
                    SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_apartments,
                    SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_apartments
                FROM Apartment
            """)
            return Cursor.fetchone()

        finally:
            Connection.close()

    @staticmethod
    def GetOccupancyByLocation():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    l.city,
                    COUNT(a.apartment_id) AS total_apartments,
                    SUM(CASE WHEN a.status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied_apartments,
                    SUM(CASE WHEN a.status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_apartments,
                    SUM(CASE WHEN a.status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_apartments
                FROM Location l
                LEFT JOIN Apartment a
                ON l.location_id = a.location_id
                GROUP BY l.location_id, l.city
                ORDER BY l.city
            """)
            return Cursor.fetchall()

        finally:
            Connection.close()
        
    @staticmethod
    def GetOpenMaintenanceRequests():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, tenant_id, apartment_id, description, priority, status, reported_date
                FROM MaintenanceRequest
                WHERE status IN ('REPORTED', 'IN_PROGRESS')
                ORDER BY reported_date
            """)
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def GetMaintenanceCostSummary():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    COUNT(request_id) AS total_requests,
                    COALESCE(SUM(cost), 0) AS total_maintenance_cost
                FROM MaintenanceRequest
                WHERE status = 'RESOLVED'
            """)
            return Cursor.fetchone()

        finally:
            Connection.close()

    @staticmethod
    def GetComplaintsSummary():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT status, COUNT(*) AS total
                FROM Complaint
                GROUP BY status
                ORDER BY status
            """)
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def GetTenantPaymentHistory(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Tenant Id is invalid.")
        
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT p.payment_id, p.amount, p.payment_date, p.method
                FROM Payment p
                INNER JOIN Invoice i ON p.invoice_id = i.invoice_id
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                WHERE l.tenant_id = ?
                ORDER BY p.payment_date
            """, (TenantId,))
            return Cursor.fetchall()

        finally:
            Connection.close()