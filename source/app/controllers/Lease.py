from source.app.services.LeaseService import LeaseService


class LeaseController:

    @staticmethod
    def CreateLease(*args):
        return LeaseService.CreateLeaseWithInitialInvoice(*args)

    @staticmethod
    def GetLeaseByNI(ni):
        return LeaseService.GetLeaseByNI(ni)

    @staticmethod
    def GenerateInvoice(lease_id):
        return LeaseService.GenerateNextInvoice(lease_id)

    @staticmethod
    def TerminateLease(ni):
        return LeaseService.TerminateLease(ni)

    @staticmethod
    def GetAllLeases():
        return LeaseService.GetAllLeases()