from source.app.services.LeaseService import LeaseService


class LeaseController:

    @staticmethod
    def CreateLease(*args):
        return LeaseService.CreateLeaseWithInitialInvoice(*args)

    @staticmethod
    def GetLeaseByNI(ni):
        return LeaseService.GetLeaseByNI(ni)

    @staticmethod
    def GenerateInvoice(lease_id, due_date):
        return LeaseService.GenerateNextInvoice(lease_id, due_date)

    @staticmethod
    def TerminateLease(ni):
        return LeaseService.TerminateLease(ni)

    @staticmethod
    def GetAllLeases():
        return LeaseService.GetAllLeases()
    
    @staticmethod
    def GetLeasesByLocation(LocationId):
        return LeaseService.GetLeasesByLocation(LocationId)