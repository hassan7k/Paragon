import sqlite3
from source.app.databases.Database import Get_Connection


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
