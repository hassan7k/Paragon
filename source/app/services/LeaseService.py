import sqlite3
from datetime import date, datetime, timedelta
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

            Cursor.execute("""
                INSERT INTO Lease (
                    tenant_id, apartment_id, start_date, end_date,
                    deposit_amount, agreed_monthly_rent, status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
            """, (TenantId, ApartmentId, StartDate, EndDate, Deposit, MonthlyRent))
            LeaseId = Cursor.lastrowid

            Cursor.execute("""
                INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (LeaseId, FirstDueDate, MonthlyRent))

            Cursor.execute("""
                UPDATE Apartment SET status = 'OCCUPIED'
                WHERE apartment_id = ?
            """, (ApartmentId,))

            Connection.commit()
            return LeaseId

        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            raise ValueError("Database errors while creating lease.") from FailError
        except:
            Connection.rollback()
            raise
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  NORMAL TERMINATION  (lease reached its natural end date)
    # ------------------------------------------------------------------
    @staticmethod
    def TerminateLease(LeaseId: int):
        """
        Terminate a lease that has reached its natural end.
        No penalty is applied.
        """
        if LeaseId <= 0:
            raise ValueError("Invalid Lease Id.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT apartment_id, end_date, status
                FROM Lease WHERE lease_id = ?
            """, (LeaseId,))
            Row = Cursor.fetchone()
            if not Row:
                raise ValueError("Lease not found.")

            ApartmentId, EndDate, Status = Row
            if Status != "ACTIVE":
                raise ValueError("Only ACTIVE leases can be terminated.")

            # Standard termination is only allowed on or after the natural end date.
            # If the tenant is leaving early, the Early Terminate flow must be used.
            OriginalEnd = datetime.strptime(EndDate, "%Y-%m-%d").date()
            if date.today() < OriginalEnd:
                raise ValueError(
                    f"Lease end date ({EndDate}) has not been reached yet. "
                    "Use 'Early Terminate' for leases that end before their contract date."
                )

            Cursor.execute("""
                UPDATE Lease SET status = 'TERMINATED', end_date = DATE('now')
                WHERE lease_id = ?
            """, (LeaseId,))

            Cursor.execute("""
                UPDATE Apartment SET status = 'AVAILABLE'
                WHERE apartment_id = ?
            """, (ApartmentId,))

            Connection.commit()

        except:
            Connection.rollback()
            raise
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  EARLY TERMINATION  (tenant leaves before end date)
    # ------------------------------------------------------------------
    @staticmethod
    def TerminateLeaseEarly(LeaseId: int, NoticeGivenDate: str) -> dict:
        """
        Terminate a lease early with 1-month notice requirement and 5% penalty.

        Parameters:
            LeaseId        : ID of the lease to terminate
            NoticeGivenDate: 'YYYY-MM-DD' — date tenant gave notice

        Returns dict:
            is_early          : bool
            penalty_amount    : float (0.0 if not early)
            penalty_invoice_id: int or None

        Raises ValueError if:
            - Notice period < 30 days
            - Lease not ACTIVE
            - Lease not found
        """
        if LeaseId <= 0:
            raise ValueError("Invalid Lease Id.")

        try:
            NoticeDate = datetime.strptime(NoticeGivenDate, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Notice date must be in format YYYY-MM-DD.")

        Today = date.today()

        # Enforce 1-month notice period
        if (Today - NoticeDate).days < 30:
            DaysShort = 30 - (Today - NoticeDate).days
            raise ValueError(
                f"Tenant must give at least 1 month notice. "
                f"{DaysShort} more day(s) required before termination."
            )

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT apartment_id, end_date, agreed_monthly_rent, status
                FROM Lease WHERE lease_id = ?
            """, (LeaseId,))
            Row = Cursor.fetchone()
            if not Row:
                raise ValueError("Lease not found.")

            ApartmentId, EndDate, MonthlyRent, Status = Row

            if Status != "ACTIVE":
                raise ValueError("Only ACTIVE leases can be terminated.")

            # Determine if this is truly early
            OriginalEnd = datetime.strptime(EndDate, "%Y-%m-%d").date()
            IsEarly = Today < OriginalEnd

            PenaltyAmount = round(MonthlyRent * 0.05, 2) if IsEarly else 0.0
            PenaltyInvoiceId = None

            # Create penalty invoice if leaving early
            if IsEarly:
                Cursor.execute("""
                    INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                    VALUES (?, DATE('now'), ?, 'PENDING')
                """, (LeaseId, PenaltyAmount))
                PenaltyInvoiceId = Cursor.lastrowid

            # Terminate lease
            Cursor.execute("""
                UPDATE Lease SET status = 'TERMINATED', end_date = DATE('now')
                WHERE lease_id = ?
            """, (LeaseId,))

            # Release apartment
            Cursor.execute("""
                UPDATE Apartment SET status = 'AVAILABLE'
                WHERE apartment_id = ?
            """, (ApartmentId,))

            Connection.commit()

            return {
                "is_early": IsEarly,
                "penalty_amount": PenaltyAmount,
                "penalty_invoice_id": PenaltyInvoiceId
            }

        except:
            Connection.rollback()
            raise
        finally:
            Connection.close()

    # ------------------------------------------------------------------
    #  QUERIES
    # ------------------------------------------------------------------
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
