import sqlite3
from source.app.databases.database import Get_Connection


class MaintenanceService:

    @staticmethod
    def CreateMaintenanceRequest(TenantId: int, ApartmentId: int, Description: str, Priority: str) -> int:
        if TenantId <= 0:
            raise ValueError("Tenant ID is invalid.")
        if ApartmentId <= 0:
            raise ValueError("Apartment ID is invalid.")
        if not Description or not Description.strip():
            raise ValueError("Description is required.")

        Priority = Priority.upper()
        ValidPriorities = ("LOW", "MEDIUM", "HIGH")
        if Priority not in ValidPriorities:
            raise ValueError("Priority must be LOW, MEDIUM, or HIGH.")

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
                raise ValueError("Tenant ID or Apartment ID does not exist.") from FailError

            raise ValueError("Database integrity error while creating maintenance request.") from FailError

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def GetAllRequests():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, tenant_id, apartment_id, description, priority,
                       status, assigned_worker, scheduled_date, scheduled_time,
                       resolution_notes, time_taken_hours, reported_date,
                       resolved_date, cost
                FROM MaintenanceRequest
                ORDER BY
                    CASE priority
                        WHEN 'HIGH' THEN 1
                        WHEN 'MEDIUM' THEN 2
                        WHEN 'LOW' THEN 3
                    END,
                    request_id DESC
            """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def GetRequestById(RequestId: int):
        if RequestId <= 0:
            raise ValueError("Request ID is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, tenant_id, apartment_id, description, priority,
                       status, assigned_worker, scheduled_date, scheduled_time,
                       resolution_notes, time_taken_hours, reported_date,
                       resolved_date, cost
                FROM MaintenanceRequest
                WHERE request_id = ?
            """, (RequestId,))
            return Cursor.fetchone()
        finally:
            Connection.close()

    @staticmethod
    def GetRequestsByStatus(Status: str):
        Status = Status.upper()
        ValidStatuses = ("REPORTED", "SCHEDULED", "IN_PROGRESS", "RESOLVED")
        if Status not in ValidStatuses:
            raise ValueError("Invalid status.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, tenant_id, apartment_id, description, priority,
                       status, assigned_worker, scheduled_date, scheduled_time,
                       resolution_notes, time_taken_hours, reported_date,
                       resolved_date, cost
                FROM MaintenanceRequest
                WHERE status = ?
                ORDER BY request_id DESC
            """, (Status,))
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def UpdatePriority(RequestId: int, NewPriority: str):
        if RequestId <= 0:
            raise ValueError("Request ID is invalid.")

        NewPriority = NewPriority.upper()
        ValidPriorities = ("LOW", "MEDIUM", "HIGH")
        if NewPriority not in ValidPriorities:
            raise ValueError("Priority must be LOW, MEDIUM, or HIGH.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE MaintenanceRequest
                SET priority = ?
                WHERE request_id = ?
            """, (NewPriority, RequestId))

            if Cursor.rowcount == 0:
                raise ValueError("Maintenance request not found.")

            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def ScheduleMaintenance(RequestId: int, AssignedWorker: str, ScheduledDate: str, ScheduledTime: str):
        if RequestId <= 0:
            raise ValueError("Request ID is invalid.")
        if not AssignedWorker or not AssignedWorker.strip():
            raise ValueError("Assigned worker is required.")
        if not ScheduledDate or not ScheduledDate.strip():
            raise ValueError("Scheduled date is required.")
        if not ScheduledTime or not ScheduledTime.strip():
            raise ValueError("Scheduled time is required.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE MaintenanceRequest
                SET assigned_worker = ?,
                    scheduled_date = ?,
                    scheduled_time = ?,
                    status = 'SCHEDULED'
                WHERE request_id = ?
            """, (AssignedWorker.strip(), ScheduledDate.strip(), ScheduledTime.strip(), RequestId))

            if Cursor.rowcount == 0:
                raise ValueError("Maintenance request not found.")

            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def StartMaintenance(RequestId: int):
        if RequestId <= 0:
            raise ValueError("Request ID is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE MaintenanceRequest
                SET status = 'IN_PROGRESS'
                WHERE request_id = ?
            """, (RequestId,))

            if Cursor.rowcount == 0:
                raise ValueError("Maintenance request not found.")

            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def ResolveMaintenanceRequest(RequestId: int, ResolutionNotes: str, TimeTakenHours: float, Cost: float):
        if RequestId <= 0:
            raise ValueError("Request ID is invalid.")
        if not ResolutionNotes or not ResolutionNotes.strip():
            raise ValueError("Resolution notes are required.")
        if TimeTakenHours < 0:
            raise ValueError("Time taken cannot be negative.")
        if Cost < 0:
            raise ValueError("Cost cannot be negative.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE MaintenanceRequest
                SET status = 'RESOLVED',
                    resolution_notes = ?,
                    time_taken_hours = ?,
                    cost = ?,
                    resolved_date = DATE('now')
                WHERE request_id = ?
            """, (ResolutionNotes.strip(), TimeTakenHours, Cost, RequestId))

            if Cursor.rowcount == 0:
                raise ValueError("Maintenance request not found.")

            Connection.commit()

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def GetRequestsByTenant(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Tenant ID is invalid.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT request_id, tenant_id, apartment_id, description, priority,
                       status, assigned_worker, scheduled_date, scheduled_time,
                       resolution_notes, time_taken_hours, reported_date,
                       resolved_date, cost
                FROM MaintenanceRequest
                WHERE tenant_id = ?
                ORDER BY reported_date DESC
            """, (TenantId,))
            return Cursor.fetchall()
        finally:
            Connection.close()
