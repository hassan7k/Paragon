import sqlite3
from datetime import date
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
    def TerminateLease(ni: str):
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                SELECT l.lease_id, l.apartment_id
                FROM Lease l
                INNER JOIN Tenant t ON l.tenant_id = t.tenant_id
                WHERE t.ni_number = ? AND l.status = 'ACTIVE'
            """, (ni,))
            lease = Cursor.fetchone()

            if not lease:
                raise ValueError("Active lease not found for tenant.")

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