import sqlite3
from datetime import date
from source.app.databases.database import Get_Connection

# 

class InvoiceService:

    @staticmethod
    def CreateInvoice(
        LeaseId: int,
        DueDate: str,
        AmountDue: float
    ) -> int:
        if LeaseId <= 0:
            raise ValueError("Lease ID cannot be less than 0.")
        if not DueDate or not DueDate.strip():
            raise ValueError("Due date is required.")
        if AmountDue <= 0:
            raise ValueError("Amount due must be more than 0.")
        
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                INSERT INTO Invoice (lease_id, due_date, amount_due, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (LeaseId, DueDate.strip(), AmountDue))

            InvoiceId = Cursor.lastrowid
            Connection.commit()
            return InvoiceId
        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            Message = str(FailError)

            if "FOREIGN KEY constraint failed" in Message:
                raise ValueError("Lease doesn't exist.") from FailError
            raise ValueError("Database integrity error while creating invoice.") from FailError
        
        except Exception:
            Connection.rollback()
            raise

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
                SELECT invoice_id, lease_id, due_date, amount_due, status
                FROM Invoice
                WHERE invoice_id = ?
            """, (InvoiceId,))
            return Cursor.fetchone()

        finally:
            Connection.close()
    
    @staticmethod
    def GetInvoiceByLease(LeaseId: int):
        if LeaseId <= 0:
            raise ValueError("Invalid lease ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT invoice_id, due_date, amount_due, status
                FROM Invoice
                WHERE lease_id = ?
                ORDER BY due_date
            """, (LeaseId,))
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def MarkInvoicePaid(InvoiceId: int):
        if InvoiceId <= 0:
            raise ValueError("Invalid invoice ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE Invoice
                SET status = 'PAID'
                WHERE invoice_id = ?
            """, (InvoiceId,))

            if Cursor.rowcount == 0:
                raise ValueError("Invoice not found.")

            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()


    @staticmethod
    def MarkInvoiceOverdue(InvoiceId: int):
        if InvoiceId <= 0:
            raise ValueError("Invalid invoice ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE Invoice
                SET status = 'OVERDUE'
                WHERE invoice_id = ? AND status = 'PENDING'
            """, (InvoiceId,))

            if Cursor.rowcount == 0:
                raise ValueError("Invoice not found or could not be marked overdue.")

            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()
    
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