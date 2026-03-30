from source.app.services.TenantService import TenantService


class ComplaintController:

    @staticmethod
    def AddComplaint(ni, description):
        return TenantService.AddComplaint(ni, description)

    @staticmethod
    def GetComplaints():
        return TenantService.GetComplaints()