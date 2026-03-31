import sqlite3
from source.app.databases.database import Get_Connection

class MaintenanceService:

    @staticmethod
    def CreateMaintenanceRequest(TenantId: int, ApartmentId: int, Description: str, Priority: str) -> int:
        if TenantId <= 0:
            raise ValueError("Tenant Id is invalid.")
        if ApartmentId <= 0:
            raise ValueError("Apartment Id is invalid.")
        if not Description or not Description.strip():
            raise ValueError("No valid descripton given.")

        ValidPriorities = ("LOW", "MEDIUM", "HIGH")
        if Priority not in ValidPriorities:
            raise ValueError("Invalid priority.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                INSERT INTO MaintenanceRequest (
                    tenant_id, apartment_id, description, priority, status
                )
                VALUES (?, ?, ?, ?, 'REPORTED')
            """, (TenantId, ApartmentId, Description.strip(), Priority))
            RequestId = Cursor.lastrowid
            Connection.commit()
            return RequestId

        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            Message = str(FailError)

            if "FOREIGN KEY constraint failed" in Message:
                raise ValueError("Tenant or apartment does not exist.") from FailError

            raise ValueError("Database integrity error while creating maintenance request.") from FailError

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def UpdateMaintenanceStatus(RequestId: int, NewStatus: str):
        if RequestId <= 0:
            raise ValueError("Request Id is invalid")

        ValidStatuses = ("REPORTED", "IN_PROGRESS", "RESOLVED")
        if NewStatus not in ValidStatuses:
            raise ValueError("Invalid maintenance status.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE MaintenanceRequest
                SET status = ?
                WHERE request_id = ?
            """, (NewStatus, RequestId))
            if Cursor.rowcount == 0:
                raise ValueError("Maintenance request not found.")
            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def ResolveMaintenanceRequest(RequestId: int, Cost: float):
        if RequestId <= 0:
            raise ValueError("Request Id is invalid.")
        if Cost < 0:
            raise ValueError("Cost cannot be negative.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE MaintenanceRequest
                SET status = 'RESOLVED',
                    cost = ?,
                    resolved_date = DATE('now')
                WHERE request_id = ?
            """, (Cost, RequestId))
            if Cursor.rowcount == 0:
                raise ValueError("Maintenance request not found.")
            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def GetRequestById(RequestId: int):
        if RequestId <= 0:
            raise ValueError("Request Id is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, tenant_id, apartment_id, description, priority,
                   status, reported_date, resolved_date, cost
                FROM MaintenanceRequest
                WHERE request_id = ?
                """
            , (RequestId,))
            return Cursor.fetchone()

        finally:
            Connection.close()

    @staticmethod
    def GetRequestsByTenant(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Tenant Id is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, apartment_id, description, priority, status,
                       reported_date, resolved_date, cost
                FROM MaintenanceRequest
                WHERE tenant_id = ?
                ORDER BY reported_date
            """, (TenantId,))
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def GetRequestsByApartment(ApartmentId: int):
        if ApartmentId <= 0:
            raise ValueError("Apartment Id is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, tenant_id, description, priority, status,
                       reported_date, resolved_date, cost
                FROM MaintenanceRequest
                WHERE apartment_id = ?
                ORDER BY reported_date
            """, (ApartmentId,))
            return Cursor.fetchall()

        finally:
            Connection.close()
