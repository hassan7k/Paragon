import sqlite3
from source.app.databases.database import Get_Connection


class ReportingService:
    """
    All reporting methods accept an optional LocationId parameter.
    - LocationId=None  → MANAGER view: data across all locations
    - LocationId=int   → ADMIN view:   data scoped to that location only
    """

    # ------------------------------------------------------------------
    #  RENT COLLECTION
    # ------------------------------------------------------------------
    @staticmethod
    def GetCollectedVsPendingRent(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT
                        COALESCE(SUM(CASE WHEN i.status = 'PAID'
                            THEN i.amount_due ELSE 0 END), 0) AS collected,
                        COALESCE(SUM(CASE WHEN i.status IN ('PENDING','OVERDUE')
                            THEN i.amount_due ELSE 0 END), 0) AS pending
                    FROM Invoice i
                    JOIN Lease l ON i.lease_id = l.lease_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    WHERE a.location_id = ?
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT
                        COALESCE(SUM(CASE WHEN status = 'PAID'
                            THEN amount_due ELSE 0 END), 0),
                        COALESCE(SUM(CASE WHEN status IN ('PENDING','OVERDUE')
                            THEN amount_due ELSE 0 END), 0)
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

    # ------------------------------------------------------------------
    #  OVERDUE INVOICES
    # ------------------------------------------------------------------
    @staticmethod
    def GetOverdueInvoices(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT i.invoice_id, i.lease_id, i.due_date, i.amount_due, i.status,
                           t.first_name || ' ' || t.last_name AS tenant_name, loc.city
                    FROM Invoice i
                    JOIN Lease l ON i.lease_id = l.lease_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    JOIN Location loc ON a.location_id = loc.location_id
                    JOIN Tenant t ON l.tenant_id = t.tenant_id
                    WHERE i.status = 'OVERDUE'
                      AND a.location_id = ?
                    ORDER BY i.due_date
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT i.invoice_id, i.lease_id, i.due_date, i.amount_due, i.status,
                           t.first_name || ' ' || t.last_name AS tenant_name, loc.city
                    FROM Invoice i
                    JOIN Lease l ON i.lease_id = l.lease_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    JOIN Location loc ON a.location_id = loc.location_id
                    JOIN Tenant t ON l.tenant_id = t.tenant_id
                    WHERE i.status = 'OVERDUE'
                    ORDER BY i.due_date
                """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  OCCUPANCY
    # ------------------------------------------------------------------
    @staticmethod
    def GetOccupancySummary(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT
                        COUNT(apartment_id),
                        SUM(CASE WHEN status = 'OCCUPIED'    THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'AVAILABLE'   THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END)
                    FROM Apartment
                    WHERE location_id = ?
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT
                        COUNT(apartment_id),
                        SUM(CASE WHEN status = 'OCCUPIED'    THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'AVAILABLE'   THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END)
                    FROM Apartment
                """)
            return Cursor.fetchone()
        finally:
            Connection.close()

    @staticmethod
    def GetOccupancyByLocation(LocationId=None):
        """
        Manager: all cities. Admin: only their city row.
        """
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT l.city,
                        COUNT(a.apartment_id),
                        SUM(CASE WHEN a.status = 'OCCUPIED'    THEN 1 ELSE 0 END),
                        SUM(CASE WHEN a.status = 'AVAILABLE'   THEN 1 ELSE 0 END),
                        SUM(CASE WHEN a.status = 'MAINTENANCE' THEN 1 ELSE 0 END)
                    FROM Location l
                    LEFT JOIN Apartment a ON l.location_id = a.location_id
                    WHERE l.location_id = ?
                    GROUP BY l.location_id, l.city
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT l.city,
                        COUNT(a.apartment_id),
                        SUM(CASE WHEN a.status = 'OCCUPIED'    THEN 1 ELSE 0 END),
                        SUM(CASE WHEN a.status = 'AVAILABLE'   THEN 1 ELSE 0 END),
                        SUM(CASE WHEN a.status = 'MAINTENANCE' THEN 1 ELSE 0 END)
                    FROM Location l
                    LEFT JOIN Apartment a ON l.location_id = a.location_id
                    GROUP BY l.location_id, l.city
                    ORDER BY l.city
                """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  MAINTENANCE
    # ------------------------------------------------------------------
    @staticmethod
    def GetOpenMaintenanceRequests(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT m.request_id, m.apartment_id, m.description,
                           m.priority, m.status, m.reported_date, loc.city
                    FROM MaintenanceRequest m
                    JOIN Apartment a ON m.apartment_id = a.apartment_id
                    JOIN Location loc ON a.location_id = loc.location_id
                    WHERE m.status IN ('REPORTED','IN_PROGRESS')
                      AND a.location_id = ?
                    ORDER BY m.reported_date
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT m.request_id, m.apartment_id, m.description,
                           m.priority, m.status, m.reported_date, loc.city
                    FROM MaintenanceRequest m
                    JOIN Apartment a ON m.apartment_id = a.apartment_id
                    JOIN Location loc ON a.location_id = loc.location_id
                    WHERE m.status IN ('REPORTED','IN_PROGRESS')
                    ORDER BY m.reported_date
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
                        COUNT(m.request_id),
                        COALESCE(SUM(m.cost), 0)
                    FROM MaintenanceRequest m
                    JOIN Apartment a ON m.apartment_id = a.apartment_id
                    WHERE m.status = 'RESOLVED'
                      AND a.location_id = ?
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT COUNT(request_id), COALESCE(SUM(cost), 0)
                    FROM MaintenanceRequest
                    WHERE status = 'RESOLVED'
                """)
            return Cursor.fetchone()
        finally:
            Connection.close()

    @staticmethod
    def GetMaintenanceSummaryByLocation(LocationId=None):
        """
        Returns open count, resolved count, total cost, avg resolution days.
        Used in dashboard for Admin/Manager maintenance cards.
        """
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT
                        COUNT(CASE WHEN m.status IN ('REPORTED','IN_PROGRESS') THEN 1 END),
                        COUNT(CASE WHEN m.status = 'RESOLVED' THEN 1 END),
                        COALESCE(SUM(m.cost), 0),
                        ROUND(AVG(
                            CASE WHEN m.resolved_date IS NOT NULL
                            THEN julianday(m.resolved_date) - julianday(m.reported_date)
                            END
                        ), 1)
                    FROM MaintenanceRequest m
                    JOIN Apartment a ON m.apartment_id = a.apartment_id
                    WHERE a.location_id = ?
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT
                        COUNT(CASE WHEN status IN ('REPORTED','IN_PROGRESS') THEN 1 END),
                        COUNT(CASE WHEN status = 'RESOLVED' THEN 1 END),
                        COALESCE(SUM(cost), 0),
                        ROUND(AVG(
                            CASE WHEN resolved_date IS NOT NULL
                            THEN julianday(resolved_date) - julianday(reported_date)
                            END
                        ), 1)
                    FROM MaintenanceRequest
                """)
            return Cursor.fetchone()
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  COMPLAINTS
    # ------------------------------------------------------------------
    @staticmethod
    def GetComplaintsSummary(LocationId=None):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT c.status, COUNT(*) AS total
                    FROM Complaint c
                    JOIN Tenant t ON c.tenant_id = t.tenant_id
                    JOIN Lease l ON t.tenant_id = l.tenant_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
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
    def GetComplaintsByLocation(LocationId=None):
        """Full complaint list scoped by location."""
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT c.complaint_id,
                           t.first_name || ' ' || t.last_name,
                           t.ni_number,
                           c.description, c.status, c.created_at,
                           loc.city
                    FROM Complaint c
                    JOIN Tenant t ON c.tenant_id = t.tenant_id
                    JOIN Lease l ON t.tenant_id = l.tenant_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    JOIN Location loc ON a.location_id = loc.location_id
                    WHERE a.location_id = ?
                    ORDER BY c.created_at DESC
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT c.complaint_id,
                           t.first_name || ' ' || t.last_name,
                           t.ni_number,
                           c.description, c.status, c.created_at,
                           COALESCE(loc.city, 'N/A')
                    FROM Complaint c
                    JOIN Tenant t ON c.tenant_id = t.tenant_id
                    LEFT JOIN Lease l ON t.tenant_id = l.tenant_id
                    LEFT JOIN Apartment a ON l.apartment_id = a.apartment_id
                    LEFT JOIN Location loc ON a.location_id = loc.location_id
                    ORDER BY c.created_at DESC
                """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  ALL INVOICES  (for admin invoice management tab)
    # ------------------------------------------------------------------
    @staticmethod
    def GetAllInvoices(LocationId=None):
        """
        Full invoice list with tenant name, apartment, city and status.
        Used in the Admin/Manager Invoices tab.
        """
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if LocationId:
                Cursor.execute("""
                    SELECT i.invoice_id,
                           t.first_name || ' ' || t.last_name AS tenant,
                           a.apartment_number, loc.city,
                           i.due_date, i.amount_due, i.status
                    FROM Invoice i
                    JOIN Lease l    ON i.lease_id    = l.lease_id
                    JOIN Tenant t   ON l.tenant_id   = t.tenant_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    JOIN Location loc ON a.location_id = loc.location_id
                    WHERE a.location_id = ?
                    ORDER BY i.due_date DESC
                """, (LocationId,))
            else:
                Cursor.execute("""
                    SELECT i.invoice_id,
                           t.first_name || ' ' || t.last_name AS tenant,
                           a.apartment_number, loc.city,
                           i.due_date, i.amount_due, i.status
                    FROM Invoice i
                    JOIN Lease l    ON i.lease_id    = l.lease_id
                    JOIN Tenant t   ON l.tenant_id   = t.tenant_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    JOIN Location loc ON a.location_id = loc.location_id
                    ORDER BY i.due_date DESC
                """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  TENANT PAYMENT HISTORY
    # ------------------------------------------------------------------
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
