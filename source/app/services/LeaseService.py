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