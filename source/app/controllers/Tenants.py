from source.app.services.TenantService import TenantService


class TenantController:

    # ---------------- TENANT ----------------
    @staticmethod
    def AddTenant(*args):
        return TenantService.AddTenant(*args)
    
    @staticmethod
    def AddTenantExtended(ni, first, last, phone, email, occupation, reference,
                          requirement="", lease_years="", emergency_contact="", notes=""):
        return TenantService.AddTenant(ni, first, last, phone, email, occupation, reference)

    @staticmethod
    def GetTenant(ni):
        return TenantService.GetTenant(ni)
    
    @staticmethod
    def GetTenantByNI(ni):
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