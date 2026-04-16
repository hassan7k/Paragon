from source.app.services.AuthService import AuthService
from source.app.services.TenantService import TenantService
from source.app.services.ApartmentService import ApartmentService
from source.app.services.LeaseService import LeaseService
from source.app.services.InvoiceService import InvoiceService
from source.app.services.ReportingService import ReportingService
from source.app.services.ComplaintService import ComplaintService
from source.app.databases.database import Get_Connection


def _Loc(UserRole: str, UserLocationId: int):
    """
    Returns the LocationId to use for scoped queries.
    ADMIN  → their own location_id
    MANAGER → None (no filter, sees all locations)
    """
    return UserLocationId if UserRole == "ADMIN" else None


def _AssertLeaseOwnership(LeaseId: int, UserRole: str, UserLocationId: int):
    """ADMIN only: raise PermissionError if the lease's apartment is not in their location."""
    if UserRole != "ADMIN":
        return
    Connection = Get_Connection()
    try:
        Cursor = Connection.cursor()
        Cursor.execute("""
            SELECT a.location_id FROM Lease l
            JOIN Apartment a ON l.apartment_id = a.apartment_id
            WHERE l.lease_id = ?
        """, (LeaseId,))
        Row = Cursor.fetchone()
        if not Row:
            raise ValueError("Lease not found.")
        if Row[0] != UserLocationId:
            raise PermissionError("You do not have permission to modify this lease.")
    finally:
        Connection.close()


def _AssertComplaintOwnership(ComplaintId: int, UserRole: str, UserLocationId: int):
    """ADMIN only: raise PermissionError if the complaint's tenant has no lease in their location."""
    if UserRole != "ADMIN":
        return
    Connection = Get_Connection()
    try:
        Cursor = Connection.cursor()
        # Use the most recent lease to determine the tenant's location
        Cursor.execute("""
            SELECT a.location_id FROM Complaint c
            JOIN Lease l ON c.tenant_id = l.tenant_id
            JOIN Apartment a ON l.apartment_id = a.apartment_id
            WHERE c.complaint_id = ?
            ORDER BY l.lease_id DESC LIMIT 1
        """, (ComplaintId,))
        Row = Cursor.fetchone()
        if not Row:
            raise ValueError("Complaint not found or tenant has no lease history.")
        if Row[0] != UserLocationId:
            raise PermissionError("You do not have permission to modify this complaint.")
    finally:
        Connection.close()


def _AssertStaffOwnership(UserId: int, UserRole: str, UserLocationId: int):
    """ADMIN only: raise PermissionError if the user is not in their location."""
    if UserRole != "ADMIN":
        return
    Connection = Get_Connection()
    try:
        Cursor = Connection.cursor()
        Cursor.execute("SELECT location_id FROM Users WHERE user_id = ?", (UserId,))
        Row = Cursor.fetchone()
        if not Row:
            raise ValueError("User not found.")
        if Row[0] != UserLocationId:
            raise PermissionError("You do not have permission to modify staff at other locations.")
    finally:
        Connection.close()


def _AssertApartmentOwnership(ApartmentId: int, UserRole: str, UserLocationId: int):
    """ADMIN only: raise PermissionError if the apartment is not in their location."""
    if UserRole != "ADMIN":
        return
    Connection = Get_Connection()
    try:
        Cursor = Connection.cursor()
        Cursor.execute("SELECT location_id FROM Apartment WHERE apartment_id = ?", (ApartmentId,))
        Row = Cursor.fetchone()
        if not Row:
            raise ValueError("Apartment not found.")
        if Row[0] != UserLocationId:
            raise PermissionError("You do not have permission to modify apartments at other locations.")
    finally:
        Connection.close()


class AdminController:
    """
    Admin / Manager controller — Cem's module.

    RBAC rules applied at controller level:
      ADMIN   — full access scoped to their assigned location only
      MANAGER — full access across all locations + city expansion
    """

    # ══════════════════════════════════════════════════════
    #  TENANT MANAGEMENT
    # ══════════════════════════════════════════════════════

    @staticmethod
    def AddTenant(NI, FirstName, LastName, Phone, Email, Occupation=None, Reference=None):
        return TenantService.AddTenant(NI, FirstName, LastName, Phone, Email, Occupation, Reference)

    @staticmethod
    def GetTenants(UserRole: str, UserLocationId: int):
        """
        ADMIN  → active tenants with any lease in their location
        MANAGER → all active tenants system-wide
        Only is_active = 1 tenants are returned (deactivated ones are hidden).
        """
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if UserRole == "ADMIN":
                Cursor.execute("""
                    SELECT DISTINCT t.tenant_id, t.ni_number, t.first_name, t.last_name,
                           t.phone, t.email, t.occupation, t.tenant_references, t.created_at
                    FROM Tenant t
                    JOIN Lease l ON t.tenant_id = l.tenant_id
                    JOIN Apartment a ON l.apartment_id = a.apartment_id
                    WHERE a.location_id = ?
                      AND t.is_active = 1
                    ORDER BY t.tenant_id DESC
                """, (UserLocationId,))
            else:
                Cursor.execute("""
                    SELECT tenant_id, ni_number, first_name, last_name,
                           phone, email, occupation, tenant_references, created_at
                    FROM Tenant
                    WHERE is_active = 1
                    ORDER BY tenant_id DESC
                """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def UpdateTenant(TenantId: int, Phone: str, Email: str,
                     Occupation: str, Reference: str):
        """Update mutable contact fields (phone, email, occupation, reference)."""
        return TenantService.UpdateTenant(TenantId, Phone, Email, Occupation, Reference)

    @staticmethod
    def DeactivateTenant(TenantId: int):
        """
        Soft-delete: sets is_active = 0.
        Blocked if tenant has an active lease.
        All historical records (leases, invoices, complaints) are preserved.
        """
        return TenantService.DeactivateTenant(TenantId)

    # ══════════════════════════════════════════════════════
    #  LEASE MANAGEMENT
    # ══════════════════════════════════════════════════════

    @staticmethod
    def CreateLease(TenantId, ApartmentId, StartDate, EndDate, Deposit, MonthlyRent, FirstDueDate):
        return LeaseService.CreateLeaseWithInitialInvoice(
            TenantId, ApartmentId, StartDate, EndDate, Deposit, MonthlyRent, FirstDueDate
        )

    @staticmethod
    def TerminateLease(LeaseId: int, UserRole: str, UserLocationId: int):
        """
        Standard (natural end) termination — no penalty.
        ADMIN: only allowed if the lease's apartment is in their location.
        """
        _AssertLeaseOwnership(LeaseId, UserRole, UserLocationId)
        return LeaseService.TerminateLease(LeaseId)

    @staticmethod
    def TerminateLeaseEarly(LeaseId: int, NoticeGivenDate: str,
                            UserRole: str, UserLocationId: int) -> dict:
        """
        Early termination with 1-month notice validation and 5% penalty invoice.
        ADMIN: only allowed if the lease's apartment is in their location.
        Returns: {"is_early": bool, "penalty_amount": float, "penalty_invoice_id": int|None}
        """
        _AssertLeaseOwnership(LeaseId, UserRole, UserLocationId)
        return LeaseService.TerminateLeaseEarly(LeaseId, NoticeGivenDate)

    @staticmethod
    def GetLeases(UserRole: str, UserLocationId: int):
        """
        ADMIN  → leases for apartments in their location only
        MANAGER → all leases system-wide
        """
        if UserRole == "ADMIN":
            return LeaseService.GetLeasesByLocation(UserLocationId)
        return LeaseService.GetAllLeases()

    @staticmethod
    def GetActiveLeases():
        return LeaseService.GetActiveLeases()

    # ══════════════════════════════════════════════════════
    #  APARTMENT MANAGEMENT
    # ══════════════════════════════════════════════════════

    @staticmethod
    def CreateApartment(LocationId, ApartmentNumber, ApartmentType, Rooms, MonthlyRent):
        return ApartmentService.CreateApartment(
            LocationId, ApartmentNumber, ApartmentType, Rooms, MonthlyRent
        )

    @staticmethod
    def GetApartments(UserRole: str, UserLocationId: int):
        """
        ADMIN  → apartments at their location only
        MANAGER → apartments at all locations (grouped)
        """
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if UserRole == "ADMIN":
                Cursor.execute("""
                    SELECT a.apartment_id, a.apartment_number, a.type, a.rooms,
                           a.monthly_rent, a.status, loc.city
                    FROM Apartment a
                    JOIN Location loc ON a.location_id = loc.location_id
                    WHERE a.location_id = ?
                    ORDER BY a.apartment_number
                """, (UserLocationId,))
            else:
                Cursor.execute("""
                    SELECT a.apartment_id, a.apartment_number, a.type, a.rooms,
                           a.monthly_rent, a.status, loc.city
                    FROM Apartment a
                    JOIN Location loc ON a.location_id = loc.location_id
                    ORDER BY loc.city, a.apartment_number
                """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def GetApartmentsByLocation(LocationId: int):
        return ApartmentService.GetApartmentsByLocation(LocationId)

    @staticmethod
    def UpdateApartmentStatus(ApartmentId: int, NewStatus: str,
                              UserRole: str, UserLocationId: int):
        """ADMIN: only allowed if the apartment is in their location."""
        _AssertApartmentOwnership(ApartmentId, UserRole, UserLocationId)
        return ApartmentService.UpdateApartmentStatus(ApartmentId, NewStatus)

    # ══════════════════════════════════════════════════════
    #  LOCATION MANAGEMENT  (MANAGER ONLY)
    # ══════════════════════════════════════════════════════

    @staticmethod
    def GetAllLocations():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("SELECT location_id, city FROM Location ORDER BY city")
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def AddLocation(City: str):
        if not City or not City.strip():
            raise ValueError("City name is required.")
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("INSERT INTO Location (city) VALUES (?)", (City.strip(),))
            LocationId = Cursor.lastrowid
            Connection.commit()
            return LocationId
        except:
            Connection.rollback()
            raise
        finally:
            Connection.close()

    # ══════════════════════════════════════════════════════
    #  STAFF ACCOUNT MANAGEMENT
    # ══════════════════════════════════════════════════════

    @staticmethod
    def CreateStaffAccount(Username, Password, Role, LocationId,
                           CallerRole: str, CallerLocationId: int):
        """
        Create a new staff account.
        ADMIN: may only create accounts for their own location,
               and may not create ADMIN or MANAGER accounts.
        MANAGER: unrestricted.
        """
        if CallerRole == "ADMIN":
            if LocationId != CallerLocationId:
                raise PermissionError(
                    "Admins can only create staff accounts for their own location."
                )
            if Role in ("ADMIN", "MANAGER"):
                raise PermissionError(
                    "Admins cannot create Admin or Manager accounts. Contact a Manager."
                )
        return AuthService.CreateUser(Username, Password, Role, LocationId)

    @staticmethod
    def GetStaff(UserRole: str, UserLocationId: int):
        """
        ADMIN  → staff at their location only (active only)
        MANAGER → all active staff system-wide
        """
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            if UserRole == "ADMIN":
                Cursor.execute("""
                    SELECT u.user_id, u.username, u.role, l.city
                    FROM Users u
                    JOIN Location l ON u.location_id = l.location_id
                    WHERE u.location_id = ?
                      AND u.is_active = 1
                    ORDER BY u.user_id
                """, (UserLocationId,))
            else:
                Cursor.execute("""
                    SELECT u.user_id, u.username, u.role, l.city
                    FROM Users u
                    JOIN Location l ON u.location_id = l.location_id
                    WHERE u.is_active = 1
                    ORDER BY u.user_id
                """)
            return Cursor.fetchall()
        finally:
            Connection.close()

    @staticmethod
    def DeactivateStaff(UserId: int, UserRole: str, UserLocationId: int):
        """
        Soft-delete: sets is_active = 0 instead of hard delete.
        ADMIN: only allowed for staff in their own location.
        Preserves audit trail for records created by this user.
        """
        _AssertStaffOwnership(UserId, UserRole, UserLocationId)
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE Users SET is_active = 0 WHERE user_id = ?
            """, (UserId,))
            if Cursor.rowcount == 0:
                raise ValueError("User not found.")
            Connection.commit()
        except:
            Connection.rollback()
            raise
        finally:
            Connection.close()

    # ══════════════════════════════════════════════════════
    #  COMPLAINT MANAGEMENT
    # ══════════════════════════════════════════════════════

    @staticmethod
    def GetComplaints(UserRole: str, UserLocationId: int):
        """
        ADMIN  → complaints from tenants at their location only
        MANAGER → all complaints system-wide
        """
        Loc = _Loc(UserRole, UserLocationId)
        return ReportingService.GetComplaintsByLocation(LocationId=Loc)

    @staticmethod
    def CloseComplaint(ComplaintId: int, UserRole: str, UserLocationId: int):
        """ADMIN: only allowed if the complaint's tenant has a lease in their location."""
        _AssertComplaintOwnership(ComplaintId, UserRole, UserLocationId)
        return ComplaintService.CloseComplaint(ComplaintId)

    # ══════════════════════════════════════════════════════
    #  DASHBOARD / REPORTS  (all role-aware)
    # ══════════════════════════════════════════════════════

    @staticmethod
    def GetOccupancySummary(UserRole: str, UserLocationId: int):
        return ReportingService.GetOccupancySummary(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetOccupancyByLocation(UserRole: str, UserLocationId: int):
        return ReportingService.GetOccupancyByLocation(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetCollectedVsPendingRent(UserRole: str, UserLocationId: int):
        return ReportingService.GetCollectedVsPendingRent(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetOverdueInvoices(UserRole: str, UserLocationId: int):
        return ReportingService.GetOverdueInvoices(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetMaintenanceCostSummary(UserRole: str, UserLocationId: int):
        return ReportingService.GetMaintenanceCostSummary(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetMaintenanceSummary(UserRole: str, UserLocationId: int):
        """Returns open count, resolved count, total cost, avg resolution days."""
        return ReportingService.GetMaintenanceSummaryByLocation(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetOpenMaintenanceRequests(UserRole: str, UserLocationId: int):
        return ReportingService.GetOpenMaintenanceRequests(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetComplaintsSummary(UserRole: str, UserLocationId: int):
        return ReportingService.GetComplaintsSummary(LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetMonthlyRevenue(YearMonth: str, UserRole: str, UserLocationId: int):
        return ReportingService.GetMonthlyRevenue(YearMonth, LocationId=_Loc(UserRole, UserLocationId))

    @staticmethod
    def GetAllInvoices(UserRole: str, UserLocationId: int):
        """Full invoice list for the Invoices tab — role-scoped."""
        return ReportingService.GetAllInvoices(LocationId=_Loc(UserRole, UserLocationId))
