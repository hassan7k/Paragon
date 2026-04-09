from source.app.services.FinanceService import FinanceService


class FinanceController:

    #  INVOICES

    @staticmethod
    def GetAllInvoices():
        return FinanceService.GetAllInvoices()

    @staticmethod
    def GetInvoicesByTenant(tenant_id: int):
        return FinanceService.GetInvoicesByTenant(tenant_id)

    @staticmethod
    def GetInvoiceById(invoice_id: int):
        return FinanceService.GetInvoiceById(invoice_id)

    @staticmethod
    def GetPendingInvoices():
        return FinanceService.GetPendingInvoices()

    @staticmethod
    def GetOverdueInvoices():
        return FinanceService.GetOverdueInvoices()

    @staticmethod
    def GetPaidInvoices():
        return FinanceService.GetPaidInvoices()

    # PAYMENTS

    @staticmethod
    def GetAllPayments():
        return FinanceService.GetAllPayments()

    @staticmethod
    def GetPaymentsByInvoice(invoice_id: int):
        return FinanceService.GetPaymentsByInvoice(invoice_id)

    @staticmethod
    def GetPaymentsByTenant(tenant_id: int):
        return FinanceService.GetPaymentsByTenant(tenant_id)

    # SUMMARY

    @staticmethod
    def CalculateTotals():
        return FinanceService.CalculateTotals()

    @staticmethod
    def CalculateNetRevenue():
        return FinanceService.CalculateNetRevenue()

    @staticmethod
    def CalculateMaintenanceCost():
        return FinanceService.CalculateMaintenanceCost()
