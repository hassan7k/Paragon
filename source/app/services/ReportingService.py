import sqlite3
from source.app.databases.database import Get_Connection

class ReportingService:

    @staticmethod
    def GetCollectedVsPendingRent(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT
                        COALESCE(SUM(CASE WHEN i.status = 'PAID' THEN i.amount_due ELSE 0 END), 0) AS collected_rent,
                        COALESCE(SUM(CASE WHEN i.status IN ('PENDING', 'OVERDUE') THEN i.amount_due ELSE 0 END), 0) AS pending_rent
                    FROM Invoice i
                    JOIN Lease l ON i.lease_id = l.lease_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    WHERE a.location_id = ?
                """, (LocationId,))
            else:
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
    def GetMonthlyRevenue(YearMonth: str, LocationId=None):
        if not YearMonth or len(YearMonth) != 7:
            raise ValueError("YearMonth must be in format YYYY-MM.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT COALESCE(SUM(p.amount), 0)
                    FROM Payment p
                    JOIN Invoice i ON p.invoice_id = i.invoice_id
                    JOIN Lease l ON i.lease_id = l.lease_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    WHERE strftime('%Y-%m', p.payment_date) = ?
                      AND a.location_id = ?
                """, (YearMonth, LocationId))
            else:
                Cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM Payment
                    WHERE strftime('%Y-%m', payment_date) = ?
                """, (YearMonth,))
            return Cursor.fetchone()[0]

        finally:
            Connection.close()

    @staticmethod
    def GetOverdueInvoices(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT i.invoice_id, i.lease_id, i.due_date, i.amount_due, i.status
                    FROM Invoice i
                    JOIN Lease l ON i.lease_id = l.lease_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    WHERE i.status = 'OVERDUE' AND a.location_id = ?
                    ORDER BY i.due_date
                """, (LocationId,))
            else:
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
    def GetOccupancySummary(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            if LocationId:
                Cursor.execute("""
                    SELECT
                        COUNT(*) AS total_apartments,
                        SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied_count,
                        SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_count,
                        SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_count
                    FROM Apartment
                    WHERE location_id = ?
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT
                        COUNT(*) AS total_apartments,
                        SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied_count,
                        SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_count,
                        SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_count
                    FROM Apartment
                """)

            row = Cursor.fetchone()

            total = row[0] or 0
            occupied = row[1] or 0
            available = row[2] or 0
            maintenance = row[3] or 0

            return {
                "total_apartments": total,
                "occupied_count": occupied,
                "available_count": available,
                "maintenance_count": maintenance,
                "occupancy_rate": (occupied / total * 100) if total else 0
            }

        finally:
            Connection.close()

    @staticmethod
    def GetOccupancyByLocation(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
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
                    WHERE l.location_id = ?
                    GROUP BY l.location_id, l.city
                    ORDER BY l.city
                """, (LocationId,))
            else:
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
    def GetOpenMaintenanceRequests(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT m.request_id, m.tenant_id, m.apartment_id, m.description,
                           m.priority, m.status, m.reported_date
                    FROM MaintenanceRequest m
                    JOIN Apartment a ON m.apartment_id = a.apartment_id
                    WHERE m.status IN ('REPORTED', 'IN_PROGRESS', 'SCHEDULED')
                      AND a.location_id = ?
                    ORDER BY m.reported_date
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT request_id, tenant_id, apartment_id, description, priority, status, reported_date
                    FROM MaintenanceRequest
                    WHERE status IN ('REPORTED', 'IN_PROGRESS', 'SCHEDULED')
                    ORDER BY reported_date
                """)
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def GetMaintenanceCostSummary(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT
                        COUNT(m.request_id) AS total_requests,
                        COALESCE(SUM(m.cost), 0) AS total_maintenance_cost
                    FROM MaintenanceRequest m
                    JOIN Apartment a ON m.apartment_id = a.apartment_id
                    WHERE m.status = 'RESOLVED' AND a.location_id = ?
                """, (LocationId,))
            else:
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
    def GetMaintenanceSummaryByLocation(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT
                        SUM(CASE WHEN m.status IN ('REPORTED', 'SCHEDULED', 'IN_PROGRESS') THEN 1 ELSE 0 END) AS open_requests,
                        SUM(CASE WHEN m.status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_requests,
                        COALESCE(SUM(CASE WHEN m.status = 'RESOLVED' THEN m.cost ELSE 0 END), 0) AS total_cost,
                        ROUND(AVG(
                            CASE
                                WHEN m.status = 'RESOLVED' AND m.resolved_date IS NOT NULL
                                THEN julianday(m.resolved_date) - julianday(m.reported_date)
                            END
                        ), 1) AS avg_resolution_days
                    FROM MaintenanceRequest m
                    JOIN Apartment a ON m.apartment_id = a.apartment_id
                    WHERE a.location_id = ?
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT
                        SUM(CASE WHEN status IN ('REPORTED', 'SCHEDULED', 'IN_PROGRESS') THEN 1 ELSE 0 END) AS open_requests,
                        SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_requests,
                        COALESCE(SUM(CASE WHEN status = 'RESOLVED' THEN cost ELSE 0 END), 0) AS total_cost,
                        ROUND(AVG(
                            CASE
                                WHEN status = 'RESOLVED' AND resolved_date IS NOT NULL
                                THEN julianday(resolved_date) - julianday(reported_date)
                            END
                        ), 1) AS avg_resolution_days
                    FROM MaintenanceRequest
                """)
            Row = Cursor.fetchone()
            return (
                Row[0] or 0,
                Row[1] or 0,
                Row[2] or 0,
                Row[3]
            )

        finally:
            Connection.close()

    @staticmethod
    def GetComplaintsSummary(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT c.status, COUNT(*) AS total
                    FROM Complaint c
                    JOIN Apartment a ON c.apartment_id = a.apartment_id
                    WHERE a.location_id = ?
                    GROUP BY c.status
                    ORDER BY c.status
                """, (LocationId,))
            else:
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


    @staticmethod
    def GetAllInvoices(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            if LocationId:
                Cursor.execute("""
                    SELECT
                        i.invoice_id,
                        t.first_name || ' ' || t.last_name AS tenant_name,
                        a.apartment_number,
                        loc.city,
                        i.due_date,
                        i.amount_due,
                        i.status
                    FROM Invoice i
                    INNER JOIN Lease l ON i.lease_id = l.lease_id
                    INNER JOIN Tenant t ON l.tenant_id = t.tenant_id
                    INNER JOIN Apartment a ON l.apartment_id = a.apartment_id
                    INNER JOIN Location loc ON a.location_id = loc.location_id
                    WHERE a.location_id = ?
                    ORDER BY i.due_date DESC
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT
                        i.invoice_id,
                        t.first_name || ' ' || t.last_name AS tenant_name,
                        a.apartment_number,
                        loc.city,
                        i.due_date,
                        i.amount_due,
                        i.status
                    FROM Invoice i
                    INNER JOIN Lease l ON i.lease_id = l.lease_id
                    INNER JOIN Tenant t ON l.tenant_id = t.tenant_id
                    INNER JOIN Apartment a ON l.apartment_id = a.apartment_id
                    INNER JOIN Location loc ON a.location_id = loc.location_id
                    ORDER BY i.due_date DESC
                """)

            return Cursor.fetchall()

        finally:
            Connection.close()


    @staticmethod
    def GetComplaintsByLocation(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT
                        c.complaint_id,
                        t.first_name || ' ' || t.last_name AS tenant_name,
                        t.ni_number,
                        c.description,
                        c.status,
                        c.created_at,
                        loc.city
                    FROM Complaint c
                    INNER JOIN Tenant t ON c.tenant_id = t.tenant_id
                    INNER JOIN Apartment a ON c.apartment_id = a.apartment_id
                    INNER JOIN Location loc ON a.location_id = loc.location_id
                    WHERE a.location_id = ?
                    ORDER BY c.created_at DESC
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT
                        c.complaint_id,
                        t.first_name || ' ' || t.last_name AS tenant_name,
                        t.ni_number,
                        c.description,
                        c.status,
                        c.created_at,
                        loc.city
                    FROM Complaint c
                    INNER JOIN Tenant t ON c.tenant_id = t.tenant_id
                    LEFT JOIN Apartment a ON c.apartment_id = a.apartment_id
                    LEFT JOIN Location loc ON a.location_id = loc.location_id
                    ORDER BY c.created_at DESC
                """)
            return Cursor.fetchall()

        finally:
            Connection.close()
