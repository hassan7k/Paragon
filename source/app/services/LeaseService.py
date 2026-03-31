import sqlite3
from datetime import datetime, timedelta
from source.app.databases.database import Get_Connection


class LeaseService:

    # ---------------- CREATE LEASE ----------------
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
            raise ValueError("Invalid Tenant or Apartment ID")

        if Deposit < 0:
            raise ValueError("Deposit cannot be negative")

        if MonthlyRent <= 0:
            raise ValueError("Monthly rent must be greater than 0")

        Connection = Get_Connection()

        try:
            Cursor = Connection.cursor()

            # Check apartment availability
            Cursor.execute("""
                SELECT status FROM Apartment WHERE apartment_id = ?
            """, (ApartmentId,))
            apt = Cursor.fetchone()

            if not apt:
                raise ValueError("Apartment not found")

            if apt[0] != "AVAILABLE":
                raise ValueError("Apartment is not available")

            # Create lease
            Cursor.execute("""
                INSERT INTO Lease (
                    tenant_id, apartment_id, start_date, end_date,
                    deposit_amount, agreed_monthly_rent, status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
            """, (TenantId, ApartmentId, StartDate, EndDate, Deposit, MonthlyRent))

            LeaseId = Cursor.lastrowid

            # First invoice
            Cursor.execute("""
                INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (LeaseId, FirstDueDate, MonthlyRent))

            # Update apartment
            Cursor.execute("""
                UPDATE Apartment SET status = 'OCCUPIED'
                WHERE apartment_id = ?
            """, (ApartmentId,))

            Connection.commit()
            return LeaseId

        except sqlite3.IntegrityError as e:
            Connection.rollback()
            raise ValueError(f"Database integrity error: {e}")

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    # ---------------- GET LEASE BY NI ----------------
    @staticmethod
    def GetLeaseByNI(ni: str):
        Connection = Get_Connection()

        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
            SELECT l.lease_id, l.apartment_id, l.start_date, l.end_date,
                   l.agreed_monthly_rent, l.status
            FROM Lease l
            JOIN Tenant t ON l.tenant_id = t.tenant_id
            WHERE t.ni_number = ?
            """, (ni,))

            row = Cursor.fetchone()

            if not row:
                return None

            return {
                "lease_id": row[0],
                "apartment_id": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "rent": row[4],
                "status": row[5]
            }

        finally:
            Connection.close()

    # ---------------- GENERATE MONTHLY INVOICE ----------------
    @staticmethod
    def GenerateNextInvoice(lease_id: int):
        Connection = Get_Connection()

        try:
            Cursor = Connection.cursor()

            # Get lease rent
            Cursor.execute("""
                SELECT agreed_monthly_rent FROM Lease WHERE lease_id = ?
            """, (lease_id,))
            lease = Cursor.fetchone()

            if not lease:
                raise ValueError("Lease not found")

            rent = lease[0]

            # Last invoice date
            Cursor.execute("""
                SELECT due_date FROM Invoice
                WHERE lease_id = ?
                ORDER BY due_date DESC LIMIT 1
            """, (lease_id,))
            last = Cursor.fetchone()

            if not last:
                raise ValueError("No previous invoice found")

            last_date = datetime.strptime(last[0], "%Y-%m-%d")
            next_date = last_date + timedelta(days=30)

            Cursor.execute("""
                INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (lease_id, next_date.strftime("%Y-%m-%d"), rent))

            Connection.commit()

        finally:
            Connection.close()

    # ---------------- TERMINATE LEASE ----------------
    @staticmethod
    def TerminateLease(ni: str):
        Connection = Get_Connection()

        try:
            Cursor = Connection.cursor()

            # Get lease + rent
            Cursor.execute("""
            SELECT l.lease_id, l.agreed_monthly_rent, l.apartment_id
            FROM Lease l
            JOIN Tenant t ON l.tenant_id = t.tenant_id
            WHERE t.ni_number = ? AND l.status = 'ACTIVE'
            """, (ni,))

            lease = Cursor.fetchone()

            if not lease:
                raise ValueError("No active lease found")

            lease_id, rent, apartment_id = lease

            # Penalty = 5%
            penalty = rent * 0.05

            # Terminate lease
            Cursor.execute("""
                UPDATE Lease SET status = 'TERMINATED'
                WHERE lease_id = ?
            """, (lease_id,))

            # Apartment back to available
            Cursor.execute("""
                UPDATE Apartment SET status = 'AVAILABLE'
                WHERE apartment_id = ?
            """, (apartment_id,))

            # Create penalty invoice
            Cursor.execute("""
                INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                VALUES (?, date('now'), ?, 'PENDING')
            """, (lease_id, penalty))

            Connection.commit()
            return penalty

        finally:
            Connection.close()

    # ---------------- LIST ALL LEASES ----------------
    @staticmethod
    def GetAllLeases():
        Connection = Get_Connection()

        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
            SELECT l.lease_id, t.first_name, t.last_name,
                   l.apartment_id, l.start_date, l.end_date, l.status
            FROM Lease l
            JOIN Tenant t ON l.tenant_id = t.tenant_id
            """)

            return Cursor.fetchall()

        finally:
            Connection.close()