import sqlite3
from source.app.databases.database import Get_Connection
from source.app.services.GlobalFunctions import (
    ValidateEmail, ValidateNI, ValidatePhone
)

class TenantService:
    @staticmethod
    def AddTenant(
            NI_number: str,
            FirstName: str,
            LastName: str,
            Phone: str,
            Email: str,
            Occupation: str | None = None,
            TenantReference: str | None = None
            ) -> int:
        NI_number = ValidateNI(NI_number)
        Phone = ValidatePhone(Phone)
        Email = ValidateEmail(Email)

        if not FirstName or not FirstName.strip():
            raise ValueError("First name is required.")
        if not LastName or not LastName.strip():
            raise ValueError("Last name is required.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            # Add tenant information
            Cursor.execute("""
                INSERT INTO Tenant (ni_number, first_name, last_name, phone, email, occupation, tenant_references)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (NI_number, FirstName, LastName, Phone, Email, Occupation, TenantReference))

            Tenant_Id = Cursor.lastrowid
            Connection.commit()
            return Tenant_Id

        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            raise ValueError(f"DB integrity error: {FailError}") from FailError

        except Exception:
            Connection.rollback()

        finally:
            Connection.close()

    @staticmethod
    def UpdateTenant(TenantId: int, Phone: str, Email: str,
                     Occupation: str | None, TenantReference: str | None):
        """
        Update mutable contact fields for an existing tenant.
        NI number and name are not editable (used as primary identifiers).
        """
        if TenantId <= 0:
            raise ValueError("Invalid Tenant Id.")
        Phone = ValidatePhone(Phone)
        Email = ValidateEmail(Email)

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                UPDATE Tenant
                SET phone = ?, email = ?, occupation = ?, tenant_references = ?
                WHERE tenant_id = ? AND is_active = 1
            """, (Phone, Email, Occupation or None, TenantReference or None, TenantId))
            if Cursor.rowcount == 0:
                raise ValueError("Tenant not found or already deactivated.")
            Connection.commit()
        except:
            Connection.rollback()
            raise
        finally:
            Connection.close()

    @staticmethod
    def DeactivateTenant(TenantId: int):
        """
        Soft-delete: marks the tenant as inactive (is_active = 0).
        Blocked if the tenant still has an active lease.
        Preserves all historical lease, invoice, payment, and complaint records.
        """
        if TenantId <= 0:
            raise ValueError("Invalid Tenant Id.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            # Guard: do not deactivate a tenant who still has a running lease
            Cursor.execute("""
                SELECT COUNT(*) FROM Lease
                WHERE tenant_id = ? AND status = 'ACTIVE'
            """, (TenantId,))
            if Cursor.fetchone()[0] > 0:
                raise ValueError(
                    "Cannot deactivate a tenant with an active lease. Terminate the lease first."
                )

            Cursor.execute(
                "UPDATE Tenant SET is_active = 0 WHERE tenant_id = ?", (TenantId,)
            )
            if Cursor.rowcount == 0:
                raise ValueError("Tenant not found.")
            Connection.commit()

        except:
            Connection.rollback()
            raise
        finally:
            Connection.close()
