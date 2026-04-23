import sqlite3
from datetime import date, datetime
from source.app.databases.database import Get_Connection

class LeaseService:
    @staticmethod
    def CreateLeaseWithInitialInvoice(
            TenantId: int,
            ApartmentId: int,
            StartDate: str,
            EndDate: str,
            Deposit: float,
            MonthlyRent: float,
            FirstDueDate: str
    ) -> int:
        if TenantId <= 0 or ApartmentId <= 0:
            raise ValueError("Invalid Tenant Id or Apartment Id")
        if Deposit < 0:
            raise ValueError("Deposit cannot be negative.")
        if MonthlyRent <= 0:
            raise ValueError("Monthly rent must be above 0.")
        
        Connection = Get_Connection()

        try:
            Cursor = Connection.cursor()

            # Add lease to database
            Cursor.execute("""
                INSERT INTO Lease (
                    tenant_id, apartment_id, start_date, end_date,
                    deposit_amount, agreed_monthly_rent, status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
            """, (TenantId, ApartmentId, StartDate, EndDate, Deposit, MonthlyRent))
            LeaseId = Cursor.lastrowid

            # First month payment invoice
            Cursor.execute("""
                INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (LeaseId, FirstDueDate, MonthlyRent))

            # Set apartment to occupied
            Cursor.execute("""
                UPDATE Apartment
                SET status = 'OCCUPIED'
                WHERE apartment_id = ?
            """, (ApartmentId,))

            Connection.commit()
            return LeaseId
        
        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            raise ValueError("Database errors while creating lease.") from FailError # Probably due to foreign key failing or some kinda constraint
        
        except:
            Connection.rollback()
            raise
        
        finally:
            Connection.close()

    @staticmethod
    def GetAllLeases():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT 
                    l.lease_id,
                    t.first_name,
                    t.last_name,
                    l.apartment_id,
                    l.start_date,
                    l.end_date,
                    l.status
                FROM Lease l
                INNER JOIN Tenant t ON l.tenant_id = t.tenant_id
                ORDER BY l.start_date
            """)
            return Cursor.fetchall()
        finally:
            Connection.close()
                
    @staticmethod
    def GetLeaseByNI(ni: str):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT 
                    l.lease_id,
                    t.first_name,
                    t.last_name,
                    l.apartment_id,
                    l.start_date,
                    l.end_date,
                    l.status
                FROM Lease l
                INNER JOIN Tenant t ON l.tenant_id = t.tenant_id
                WHERE t.ni_number = ?
                ORDER BY l.start_date
            """, (ni,))
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def GenerateNextInvoice(lease_id: int, due_date: str):
        if lease_id <= 0:
            raise ValueError("Invalid lease ID.")
        
        if not due_date or not due_date.strip():
            raise ValueError("Due date is required.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT agreed_monthly_rent, status
                FROM Lease
                WHERE lease_id = ?
            """, (lease_id,))
            lease = Cursor.fetchone()

            if not lease:
                raise ValueError("Lease not found.")

            monthly_rent, status = lease

            if status != "ACTIVE":
                raise ValueError("Cannot generate invoice for inactive lease.")

            Cursor.execute("""
                INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (lease_id, due_date, monthly_rent))

            invoice_id = Cursor.lastrowid
            Connection.commit()
            return invoice_id

        except:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def TerminateLease(LeaseIdentifier):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            if isinstance(LeaseIdentifier, int):
                if LeaseIdentifier <= 0:
                    raise ValueError("Invalid lease ID.")
                Cursor.execute("""
                    SELECT lease_id, apartment_id
                    FROM Lease
                    WHERE lease_id = ? AND status = 'ACTIVE'
                """, (LeaseIdentifier,))
            else:
                Cursor.execute("""
                    SELECT l.lease_id, l.apartment_id
                    FROM Lease l
                    INNER JOIN Tenant t ON l.tenant_id = t.tenant_id
                    WHERE t.ni_number = ? AND l.status = 'ACTIVE'
                """, (LeaseIdentifier,))
            lease = Cursor.fetchone()

            if not lease:
                raise ValueError("Active lease not found.")

            lease_id, apartment_id = lease

            Cursor.execute("""
                UPDATE Lease
                SET status = 'TERMINATED'
                WHERE lease_id = ?
            """, (lease_id,))

            Cursor.execute("""
                UPDATE Apartment
                SET status = 'AVAILABLE'
                WHERE apartment_id = ?
            """, (apartment_id,))

            Connection.commit()
            return True

        except:
            Connection.rollback()
            raise

        finally:
            Connection.close()
        
    @staticmethod
    def TerminateLeaseEarly(LeaseId: int, NoticeGivenDate: str) -> dict:
        """
        Early termination:
        - Minimum 30 day notice
        - If terminated before original lease end date:
        5% penalty of monthly rent
        """

        if LeaseId <= 0:
            raise ValueError("Invalid Lease Id.")

        try:
            notice_date = datetime.strptime(NoticeGivenDate, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Notice date must be YYYY-MM-DD.")

        today = date.today()

        days_notice = (today - notice_date).days
        if days_notice < 30:
            raise ValueError(
                f"Tenant must give 30 days notice. "
                f"{30 - days_notice} more day(s) required."
            )

        Connection = Get_Connection()

        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT apartment_id, end_date, agreed_monthly_rent, status
                FROM Lease
                WHERE lease_id = ?
            """, (LeaseId,))

            row = Cursor.fetchone()

            if not row:
                raise ValueError("Lease not found.")

            apartment_id, end_date, monthly_rent, status = row

            if status != "ACTIVE":
                raise ValueError("Only ACTIVE leases can be terminated.")

            original_end = datetime.strptime(end_date, "%Y-%m-%d").date()

            is_early = today < original_end
            penalty_amount = round(float(monthly_rent) * 0.05, 2) if is_early else 0.0
            penalty_invoice_id = None

            if is_early:
                Cursor.execute("""
                    INSERT INTO Invoice (
                        lease_id, due_date, amount_due, status
                    )
                    VALUES (?, ?, ?, 'PENDING')
                """, (
                    LeaseId,
                    today.isoformat(),
                    penalty_amount
                ))
                penalty_invoice_id = Cursor.lastrowid

            Cursor.execute("""
                UPDATE Lease
                SET status = 'TERMINATED',
                    end_date = ?
                WHERE lease_id = ?
            """, (
                today.isoformat(),
                LeaseId
            ))

            Cursor.execute("""
                UPDATE Apartment
                SET status = 'AVAILABLE'
                WHERE apartment_id = ?
            """, (apartment_id,))

            Connection.commit()

            return {
                "is_early": is_early,
                "penalty_amount": penalty_amount,
                "penalty_invoice_id": penalty_invoice_id
            }

        except:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def GetAllLeases():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT l.lease_id, t.first_name || ' ' || t.last_name,
                       t.ni_number, a.apartment_number, loc.city,
                       l.start_date, l.end_date, l.agreed_monthly_rent,
                       l.deposit_amount, l.status
                FROM Lease l
                JOIN Tenant t ON l.tenant_id = t.tenant_id
                JOIN Apartment a ON l.apartment_id = a.apartment_id
                JOIN Location loc ON a.location_id = loc.location_id
                ORDER BY l.lease_id DESC
            """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def GetLeasesByLocation(LocationId: int):
        """Return all leases for apartments in a specific location."""
        if LocationId <= 0:
            raise ValueError("Invalid Location Id.")
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT l.lease_id, t.first_name || ' ' || t.last_name,
                       t.ni_number, a.apartment_number, loc.city,
                       l.start_date, l.end_date, l.agreed_monthly_rent,
                       l.deposit_amount, l.status
                FROM Lease l
                JOIN Tenant t ON l.tenant_id = t.tenant_id
                JOIN Apartment a ON l.apartment_id = a.apartment_id
                JOIN Location loc ON a.location_id = loc.location_id
                WHERE a.location_id = ?
                ORDER BY l.lease_id DESC
            """, (LocationId,))
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def GetActiveLeases():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT l.lease_id, t.first_name || ' ' || t.last_name,
                       t.ni_number, a.apartment_number, loc.city,
                       l.start_date, l.end_date, l.agreed_monthly_rent,
                       l.deposit_amount, l.status
                FROM Lease l
                JOIN Tenant t ON l.tenant_id = t.tenant_id
                JOIN Apartment a ON l.apartment_id = a.apartment_id
                JOIN Location loc ON a.location_id = loc.location_id
                WHERE l.status = 'ACTIVE'
                ORDER BY l.lease_id DESC
            """)
            return Cursor.fetchall()
        finally:
            Connection.close()
