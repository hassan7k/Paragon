import sqlite3
from source.app.databases.database import Get_Connection


class ComplaintService:

    @staticmethod
    def CreateComplaint(TenantId: int, ApartmentId: int | None, Description: str):
        if TenantId <= 0:
            raise ValueError("Tenant Id is invalid.")
        if ApartmentId is not None and ApartmentId <= 0:
            raise ValueError("Apartment Id is invalid.")
        if not Description or not Description.strip():
            raise ValueError("No valid description.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                INSERT INTO Complaint (tenant_id, apartment_id, description, status)
                VALUES (?, ?, ?, 'OPEN')
            """, (TenantId, ApartmentId, Description.strip()))
            ComplaintId = Cursor.lastrowid
            Connection.commit()
            return ComplaintId

        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            Message = str(FailError)

            if "FOREIGN KEY constraint failed" in Message:
                raise ValueError("Tenant or apartment does not exist.") from FailError

            raise ValueError("Database integrity error while creating complaint.") from FailError

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def UpdateComplaintStatus(ComplaintId: int, NewStatus: str):
        if ComplaintId <= 0:
            raise ValueError("Complaint ID is invalid.")

        ValidStatuses = ("OPEN", "CLOSED")
        if NewStatus not in ValidStatuses:
            raise ValueError("Invalid complaint status.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE Complaint
                SET status = ?
                WHERE complaint_id = ?
            """, (NewStatus, ComplaintId))
            if Cursor.rowcount == 0:
                raise ValueError("Complaint not found.")
            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def GetComplaintById(ComplaintId: int):
        if ComplaintId <= 0:
            raise ValueError("Complaint Id is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT complaint_id, tenant_id, apartment_id, description, status, created_at
                FROM Complaint
                WHERE complaint_id = ?
            """, (ComplaintId,))
            return Cursor.fetchone()

        finally:
            Connection.close()

    @staticmethod
    def GetComplaintsByTenant(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Tenant Id is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT complaint_id, tenant_id, apartment_id, description, status, created_at
                FROM Complaint
                WHERE tenant_id = ?
                ORDER BY created_at DESC
            """, (TenantId,))
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def CloseComplaint(ComplaintId: int):
        if ComplaintId <= 0:
            raise ValueError("Complaint Id is invalid")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE Complaint
                SET status = 'CLOSED'
                WHERE complaint_id = ?
            """, (ComplaintId,))
            if Cursor.rowcount == 0:
                raise ValueError("Complaint not found.")
            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def GetTenantActiveApartmentId(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Tenant Id is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT apartment_id
                FROM Lease
                WHERE tenant_id = ? AND status = 'ACTIVE'
                ORDER BY lease_id DESC
                LIMIT 1
            """, (TenantId,))
            row = Cursor.fetchone()
            return row[0] if row else None

        finally:
            Connection.close()

    @staticmethod
    def GetAllComplaints():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT complaint_id, tenant_id, apartment_id, description, status, created_at
                FROM Complaint
                ORDER BY created_at DESC
            """)
            return Cursor.fetchall()

        finally:
            Connection.close()