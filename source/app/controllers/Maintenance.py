from source.app.services.MaintenanceService import MaintenanceService


class MaintenanceController:

    @staticmethod
    def CreateRequest(TenantId: int, ApartmentId: int, Description: str, Priority: str):
        return MaintenanceService.CreateMaintenanceRequest(TenantId, ApartmentId, Description, Priority)

    @staticmethod
    def ViewAllRequests():
        return MaintenanceService.GetAllRequests()

    @staticmethod
    def ViewRequestById(RequestId: int):
        return MaintenanceService.GetRequestById(RequestId)

    @staticmethod
    def ViewRequestsByStatus(Status: str):
        return MaintenanceService.GetRequestsByStatus(Status)

    @staticmethod
    def ViewRequestsByTenant(TenantId: int):
        return MaintenanceService.GetRequestsByTenant(TenantId)

    @staticmethod
    def ChangePriority(RequestId: int, Priority: str):
        MaintenanceService.UpdatePriority(RequestId, Priority)

    @staticmethod
    def ScheduleRequest(RequestId: int, AssignedWorker: str, ScheduledDate: str, ScheduledTime: str):
        MaintenanceService.ScheduleMaintenance(RequestId, AssignedWorker, ScheduledDate, ScheduledTime)

    @staticmethod
    def StartRequest(RequestId: int):
        MaintenanceService.StartMaintenance(RequestId)

    @staticmethod
    def ResolveRequest(RequestId: int, ResolutionNotes: str, TimeTakenHours: float, Cost: float):
        MaintenanceService.ResolveMaintenanceRequest(RequestId, ResolutionNotes, TimeTakenHours, Cost)