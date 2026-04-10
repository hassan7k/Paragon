import sqlite3
from source.app.databases.database import Get_Connection


class FinanceService:

    # 1. financial summary of a location
    @staticmethod
    def GetFinancialSummaryByLocation(LocationId: int):
        if LocationId <= 0:
            raise ValueError("Invalid location ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            # total expected rent (sum of all invoices)
            Cursor.execute("""
                SELECT IFNULL(SUM(i.amount_due), 0)
                FROM Invoice i
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                INNER JOIN Apartment a ON l.apartment_id = a.apartment_id
                WHERE a.location_id = ?
            """, (LocationId,))
            TotalDue = Cursor.fetchone()[0]

            # total collected (sum of payments)
            Cursor.execute("""
                SELECT IFNULL(SUM(p.amount), 0)
                FROM Payment p
                INNER JOIN Invoice i ON p.invoice_id = i.invoice_id
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                INNER JOIN Apartment a ON l.apartment_id = a.apartment_id
                WHERE a.location_id = ?
            """, (LocationId,))
            TotalCollected = Cursor.fetchone()[0]

            # total overdue
            Cursor.execute("""
                SELECT IFNULL(SUM(i.amount_due), 0)
                FROM Invoice i
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                INNER JOIN Apartment a ON l.apartment_id = a.apartment_id
                WHERE a.location_id = ? AND i.status = 'OVERDUE'
            """, (LocationId,))
            TotalOverdue = Cursor.fetchone()[0]

            return {
                "total_due": TotalDue,
                "total_collected": TotalCollected,
                "total_overdue": TotalOverdue,
                "pending": TotalDue - TotalCollected
            }

        finally:
            Connection.close()

    # 2. tenant balance

    @staticmethod
    def GetTenantBalance(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Invalid tenant ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT 
                    IFNULL(SUM(i.amount_due), 0) -
                    IFNULL((SELECT SUM(p.amount)
                            FROM Payment p
                            INNER JOIN Invoice i2 ON p.invoice_id = i2.invoice_id
                            INNER JOIN Lease l2 ON i2.lease_id = l2.lease_id
                            WHERE l2.tenant_id = ?), 0)
                FROM Invoice i
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                WHERE l.tenant_id = ?
            """, (TenantId, TenantId))

            Balance = Cursor.fetchone()[0]
            return Balance

        finally:
            Connection.close()

    # 3. list overdue invoice

    @staticmethod
    def GetOverdueInvoices():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT invoice_id, lease_id, due_date, amount_due, status
                FROM Invoice
                WHERE status = 'OVERDUE'
                ORDER BY due_date
            """)
            return Cursor.fetchall()

        finally:
            Connection.close()

    # 4. monthly revenue report

    @staticmethod
    def GetMonthlyRevenue(Year: int, Month: int):
        if Year < 2000 or Month < 1 or Month > 12:
            raise ValueError("Invalid year or month.")

        MonthStr = f"{Year}-{Month:02d}"

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            # collected
            Cursor.execute("""
                SELECT IFNULL(SUM(amount), 0)
                FROM Payment
                WHERE strftime('%Y-%m', payment_date) = ?
            """, (MonthStr,))
            Collected = Cursor.fetchone()[0]

            # pending
            Cursor.execute("""
                SELECT IFNULL(SUM(amount_due), 0)
                FROM Invoice
                WHERE strftime('%Y-%m', due_date) = ?
                  AND status = 'PENDING'
            """, (MonthStr,))
            Pending = Cursor.fetchone()[0]

            # overdue
            Cursor.execute("""
                SELECT IFNULL(SUM(amount_due), 0)
                FROM Invoice
                WHERE strftime('%Y-%m', due_date) = ?
                  AND status = 'OVERDUE'
            """, (MonthStr,))
            Overdue = Cursor.fetchone()[0]

            return {
                "month": MonthStr,
                "collected": Collected,
                "pending": Pending,
                "overdue": Overdue
            }

        finally:
            Connection.close()

    # 5. maintanence cost summary

    @staticmethod
    def GetMaintenanceCostSummary(LocationId: int):
        if LocationId <= 0:
            raise ValueError("Invalid location ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT IFNULL(SUM(m.cost), 0)
                FROM MaintenanceRequest m
                INNER JOIN Apartment a ON m.apartment_id = a.apartment_id
                WHERE a.location_id = ?
            """, (LocationId,))
            TotalCost = Cursor.fetchone()[0]

            return TotalCost

        finally:
            Connection.close()

    # 6.full finance report of a location

    @staticmethod
    def GenerateFinanceReport(LocationId: int):
        Summary = FinanceService.GetFinancialSummaryByLocation(LocationId)
        MaintenanceCost = FinanceService.GetMaintenanceCostSummary(LocationId)

        Summary["maintenance_cost"] = MaintenanceCost
        Summary["net_revenue"] = Summary["total_collected"] - MaintenanceCost

        return Summary
    
    @staticmethod
    def GetAllInvoices():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    i.invoice_id,
                    i.lease_id,
                    l.tenant_id,
                    i.amount_due,
                    i.due_date,
                    i.status,
                    IFNULL(SUM(p.amount), 0) AS paid_amount,
                    MAX(p.payment_date) AS payment_date,
                    i.amount_due AS total_due
                FROM Invoice i
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                LEFT JOIN Payment p ON i.invoice_id = p.invoice_id
                GROUP BY i.invoice_id, i.lease_id, l.tenant_id, i.amount_due, i.due_date, i.status
                ORDER BY i.due_date
            """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def GetAllPayments():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    payment_id,
                    invoice_id,
                    amount,
                    payment_date,
                    'CARD' AS method
                FROM Payment
                ORDER BY payment_date
            """)
            return Cursor.fetchall()
        finally:
            Connection.close()
    
    @staticmethod
    def CalculateNetRevenue():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            # total collected
            Cursor.execute("""
                SELECT IFNULL(SUM(amount), 0)
                FROM Payment
            """)
            TotalCollected = Cursor.fetchone()[0]

            # total maintenance cost
            Cursor.execute("""
                SELECT IFNULL(SUM(cost), 0)
                FROM MaintenanceRequest
            """)
            TotalMaintenanceCost = Cursor.fetchone()[0]

            NetRevenue = TotalCollected - TotalMaintenanceCost
            return NetRevenue

        finally:
            Connection.close()

    @staticmethod
    def CalculateTotals():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            # total expected rent
            Cursor.execute("""
                SELECT IFNULL(SUM(amount_due), 0)
                FROM Invoice
            """)
            TotalDue = Cursor.fetchone()[0]

            # total collected
            Cursor.execute("""
                SELECT IFNULL(SUM(amount), 0)
                FROM Payment
            """)
            TotalCollected = Cursor.fetchone()[0]

            # total overdue
            Cursor.execute("""
                SELECT IFNULL(SUM(amount_due), 0)
                FROM Invoice
                WHERE status = 'OVERDUE'
            """)
            TotalOverdue = Cursor.fetchone()[0]

            return {
                "total_due": TotalDue,
                "total_collected": TotalCollected,
                "total_overdue": TotalOverdue,
                "pending": TotalDue - TotalCollected
            }

        finally:
            Connection.close()

    @staticmethod
    def CalculateMaintenanceCost():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT IFNULL(SUM(cost), 0)
                FROM MaintenanceRequest
            """)
            TotalCost = Cursor.fetchone()[0]

            return TotalCost

        finally:
            Connection.close()

    @staticmethod
    def GetInvoicesByTenant(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Invalid tenant ID.")
        
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    i.invoice_id,
                    i.lease_id,
                    l.tenant_id,
                    i.amount_due,
                    i.due_date,
                    i.status,
                    IFNULL(SUM(p.amount), 0) AS paid_amount,
                    MAX(p.payment_date) AS payment_date,
                    i.amount_due AS total_due
                FROM Invoice i
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                LEFT JOIN Payment p ON i.invoice_id = p.invoice_id
                WHERE l.tenant_id = ?
                GROUP BY i.invoice_id, i.lease_id, l.tenant_id, i.amount_due, i.due_date, i.status
                ORDER BY i.due_date
            """, (TenantId,))
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def GetPaymentsByTenant(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Invalid tenant ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT p.payment_id, p.invoice_id, p.payment_date, p.amount
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
    def GetInvoiceById(InvoiceId: int):
        if InvoiceId <= 0:
            raise ValueError("Invalid invoice ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    i.invoice_id,
                    i.lease_id,
                    l.tenant_id,
                    i.amount_due,
                    i.due_date,
                    i.status,
                    IFNULL(SUM(p.amount), 0) AS paid_amount,
                    MAX(p.payment_date) AS payment_date,
                    i.amount_due AS total_due
                FROM Invoice i
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                LEFT JOIN Payment p ON i.invoice_id = p.invoice_id
                WHERE i.invoice_id = ?
                GROUP BY i.invoice_id, i.lease_id, l.tenant_id, i.amount_due, i.due_date, i.status
            """, (InvoiceId,))
            row = Cursor.fetchone()
            return [row] if row else []
        finally:
            Connection.close()

    @staticmethod
    def GetPaymentsByInvoice(InvoiceId: int):
        if InvoiceId <= 0:
            raise ValueError("Invalid invoice ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT
                    payment_id,
                    invoice_id,
                    amount,
                    payment_date,
                    'CARD' AS method
                FROM Payment
                WHERE invoice_id = ?
                ORDER BY payment_date
            """, (InvoiceId,))
            return Cursor.fetchall()
        finally:
            Connection.close()