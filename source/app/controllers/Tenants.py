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

    # ---------------- NEW: GET ALL ----------------
    @staticmethod
    def GetAllTenants():
        return TenantService.GetAllTenants()

    # ---------------- NEW: SEARCH + FILTER ----------------
    @staticmethod
    def SearchTenants(keyword, occupation):
        return TenantService.SearchTenants(keyword, occupation)

    # ---------------- LEGACY SEARCH (KEEP SAFE) ----------------
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
    # ---------------- GET ALL ----------------
    @staticmethod
    def GetAllTenants():
        from source.app.databases.database import Get_Connection

        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT 
            tenant_id, ni_number, first_name, last_name,
            phone, email, occupation,
            apartment_requirement,
            preferred_lease_years
        FROM Tenant
        """)

        data = cur.fetchall()
        conn.close()

        return data


    # ---------------- SEARCH TENANTS ----------------
    @staticmethod
    def SearchTenants(keyword, occupation):
        from source.app.databases.database import Get_Connection

        conn = Get_Connection()
        cur = conn.cursor()

        keyword = f"%{keyword}%"
        occupation = f"%{occupation}%"

        cur.execute("""
        SELECT 
            tenant_id, ni_number, first_name, last_name,
            phone, email, occupation,
            apartment_requirement,
            preferred_lease_years
        FROM Tenant
        WHERE (ni_number LIKE ? OR first_name LIKE ? OR last_name LIKE ?)
        AND occupation LIKE ?
        """, (keyword, keyword, keyword, occupation))

        data = cur.fetchall()
        conn.close()

        return data