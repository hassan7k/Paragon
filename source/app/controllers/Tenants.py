from source.app.services.TenantService import TenantService


class TenantController:

    # ---------------- TENANT ----------------
    @staticmethod
    def AddTenant(ni, first, last, phone, email, occupation, reference):
        return TenantService.AddTenant(
            ni, first, last, phone, email, occupation, reference
        )

    @staticmethod
    def GetTenant(ni):
        return TenantService.GetTenant(ni)

    @staticmethod
    def UpdateTenant(ni, first, last, phone, email, occupation, reference):
        return TenantService.UpdateTenant(
            ni, first, last, phone, email, occupation, reference
        )

    @staticmethod
    def DeleteTenant(ni):
        return TenantService.DeleteTenant(ni)

    @staticmethod
    def GetAllTenants():
        return TenantService.GetAllTenants()

    # ---------------- COMPLAINT ----------------
    @staticmethod
    def AddComplaint(ni, description):
        return TenantService.AddComplaint(ni, description)

    # ---------------- REPORTS ----------------
    @staticmethod
    def CountTenants():
        return TenantService.CountTenants()

    @staticmethod
    def CountComplaints():
        return TenantService.CountComplaints()
    
    @staticmethod
    def SearchTenants(keyword, occupation):
        return TenantService.SearchTenants(keyword, occupation)