import sqlite3
from source.app.databases.Database import Get_Connection

class PaymentService:

    @staticmethod
    def RecordPayment(InvoiceId: int, Amount: float, Method: str):
        if InvoiceId <= 0:
            raise ValueError("Invalid invoice Id.")
        if Amount <= 0:
            raise ValueError("Payment amount must be above 0.")
        if not Method or not Method.strip():
            raise ValueError("Payment method is required.")
        
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT amount_due, status
                FROM Invoice
                WHERE invoice_id = ?
            """, (InvoiceId,))
            InvoiceData = Cursor.fetchone()

            if not InvoiceData:
                raise ValueError("Invoice data not found.")
            
            AmountDue, InvoiceStatus = InvoiceData

            if InvoiceStatus == "PAID":
                raise ValueError("Invoice is already paid.")

            if Amount != AmountDue:
                raise ValueError("Payment amount must match the invoice amount exactly.")
            
            Cursor.execute("""
                INSERT INTO Payment (invoice_id, amount, payment_date, method)
                VALUES (?, ?, DATE('now'), ?)
            """, (InvoiceId, Amount, Method.strip().upper()))

            PaymentId = Cursor.lastrowid

            # Update invoice status
            Cursor.execute("""
                UPDATE Invoice
                SET status = 'PAID'
                WHERE invoice_id = ?
            """, (InvoiceId,))

            if Cursor.rowcount == 0:
                raise ValueError("Invoice status could not be updated.")

            Connection.commit()
            return PaymentId
       
        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            Message = str(FailError)

            if "FOREIGN KEY constraint failed" in Message:
                raise ValueError("Invoice does not exist.") from FailError

            raise ValueError("Database integrity error while recording payment.") from FailError

        except Exception:
            Connection.rollback()
            raise

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
                SELECT payment_id, invoice_id, amount, payment_date, method
                FROM Payment
                WHERE invoice_id = ?
                ORDER BY payment_date
            """, (InvoiceId,))
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
                SELECT p.payment_id, p.invoice_id, p.amount, p.payment_date, p.method
                FROM Payment p
                INNER JOIN Invoice i ON p.invoice_id = i.invoice_id
                INNER JOIN Lease l ON i.lease_id = l.lease_id
                WHERE l.tenant_id = ?
                ORDER BY p.payment_date
            """, (TenantId,))
            return Cursor.fetchall()

        finally:
            Connection.close()