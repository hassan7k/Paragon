from source.app.services.ComplaintService import ComplaintService


class ComplaintController:

    @staticmethod
    def CreateComplaint(TenantId, ApartmentId, Description):
        return ComplaintService.CreateComplaint(TenantId, ApartmentId, Description)

    @staticmethod
    def GetComplaints():
        return ComplaintService.GetAllComplaints()

    @staticmethod
    def GetTenantActiveApartmentId(TenantId):
        return ComplaintService.GetTenantActiveApartmentId(TenantId)

    @staticmethod
    def CloseComplaint(ComplaintId):
        return ComplaintService.CloseComplaint(ComplaintId)
    
    @staticmethod
    def GetComplaintsByTenant(TenantId):
        rows = ComplaintService.GetAllComplaints()
        return [r for r in rows if r[1] == TenantId]