from source.app.services.TenantService import TenantService


class TenantController:

    # ---------------- TENANT ----------------
    @staticmethod
    def AddTenant(*args):
        return TenantService.AddTenant(*args)

    @staticmethod
    def GetTenant(ni):
        return TenantService.GetTenant(ni)

    @staticmethod
    def UpdateTenant(*args):
        return TenantService.UpdateTenant(*args)

    @staticmethod
    def DeleteTenant(ni):
        return TenantService.DeleteTenant(ni)

    # ---------------- GET ALL ----------------
    @staticmethod
    def GetAllTenants():
        return TenantService.GetAllTenants()

    # ---------------- SEARCH + FILTER ----------------
    @staticmethod
    def SearchTenants(keyword, occupation):
        return TenantService.SearchTenants(keyword, occupation)

    # ---------------- LEGACY ----------------
    @staticmethod
    def Search(keyword):
        return TenantService.Search(keyword)

    # ---------------- COMPLAINT ----------------
    @staticmethod
    def AddComplaint(ni, desc):
        return TenantService.AddComplaint(ni, desc)

    @staticmethod
    def GetComplaints():
        return TenantService.GetComplaints()

    # ---------------- MAINTENANCE ----------------
    @staticmethod
    def AddMaintenance(ni, apt, desc):
        return TenantService.AddMaintenance(ni, apt, desc)

    @staticmethod
    def GetMaintenance():
        return TenantService.GetMaintenance()