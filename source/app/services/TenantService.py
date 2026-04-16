import datetime
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
            TenantReference: str | None  = None 
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
            raise
        
        finally:
            Connection.close()

    @staticmethod
    def GetTenant(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM Tenant WHERE ni_number=?", (ni,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "tenant_id": row[0],
            "ni_number": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "phone": row[4],
            "email": row[5],
            "occupation": row[6],
            "tenant_references": row[7]
        }
    
    @staticmethod
    def AddTenantExtended(ni, first, last, phone, email,
                          occupation, reference,
                          requirement="", lease_years="",
                          emergency_contact="", notes=""):
        return TenantService.AddTenant(
            ni, first, last, phone, email, occupation, reference
        )

    @staticmethod
    def GetAllTenants():
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT 
            tenant_id, ni_number, first_name, last_name,
            phone, email, occupation,
            '' AS apartment_requirement,
            '' AS preferred_lease_years
        FROM Tenant
        """)

        data = cur.fetchall()
        conn.close()
        return data
    
    @staticmethod
    def SearchTenants(keyword="", occupation=""):
        conn = Get_Connection()
        cur = conn.cursor()

        keyword = f"%{keyword}%"
        occupation = f"%{occupation}%"

        cur.execute("""
        SELECT 
            tenant_id, ni_number, first_name, last_name,
            phone, email, occupation,
            '' AS apartment_requirement,
            '' AS preferred_lease_years
        FROM Tenant
        WHERE (ni_number LIKE ? OR first_name LIKE ? OR last_name LIKE ?)
        AND occupation LIKE ?
        """, (keyword, keyword, keyword, occupation))

        data = cur.fetchall()
        conn.close()
        return data
    
    @staticmethod
    def SearchTenants(keyword="", occupation=""):
        conn = Get_Connection()
        cur = conn.cursor()

        keyword = f"%{keyword}%"
        occupation = f"%{occupation}%"

        cur.execute("""
            SELECT 
            tenant_id, ni_number, first_name, last_name,
            phone, email, occupation,
            '' AS apartment_requirement,
            '' AS preferred_lease_years
            FROM Tenant
            WHERE (ni_number LIKE ? OR first_name LIKE ? OR last_name LIKE ?)
            AND occupation LIKE ?
            """, (keyword, keyword, keyword, occupation))
        data = cur.fetchall()
        conn.close()
        return data
    
    @staticmethod
    def UpdateTenant(TenantIdentifier, *args):
        conn = Get_Connection()
        cur = conn.cursor()

        try:
            if len(args) == 4:
                Phone, Email, Occupation, Reference = args

                if TenantIdentifier <= 0:
                    raise ValueError("Tenant ID is invalid.")

                Phone = ValidatePhone(Phone)
                Email = ValidateEmail(Email)

                cur.execute("""
                    UPDATE Tenant
                    SET phone = ?, email = ?, occupation = ?, tenant_references = ?
                    WHERE tenant_id = ? AND is_active = 1
                """, (Phone, Email, Occupation, Reference, TenantIdentifier))

            elif len(args) == 8:
                first, last, phone, email, occupation, reference, requirement, lease_years = args

                NI = ValidateNI(TenantIdentifier)
                phone = ValidatePhone(phone)
                email = ValidateEmail(email)

                cur.execute("""
                    UPDATE Tenant
                    SET first_name = ?, last_name = ?, phone = ?, email = ?,
                        occupation = ?, tenant_references = ?
                    WHERE ni_number = ? AND is_active = 1
                """, (
                    first, last, phone, email,
                    occupation, reference, NI
                ))
            else:
                raise TypeError("UpdateTenant expects either 5 or 9 positional arguments.")

            if cur.rowcount == 0:
                raise ValueError("Tenant not found")

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def DeactivateTenant(TenantId: int):
        if TenantId <= 0:
            raise ValueError("Tenant ID is invalid.")

        conn = Get_Connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT 1
                FROM Lease
                WHERE tenant_id = ? AND status = 'ACTIVE'
                LIMIT 1
            """, (TenantId,))
            if cur.fetchone():
                raise ValueError("Cannot deactivate a tenant with an active lease.")

            cur.execute("""
                UPDATE Tenant
                SET is_active = 0
                WHERE tenant_id = ? AND is_active = 1
            """, (TenantId,))

            if cur.rowcount == 0:
                raise ValueError("Tenant not found")

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def DeleteTenant(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM Tenant WHERE ni_number=?", (ni,))

        if cur.rowcount == 0:
            conn.close()
            raise ValueError("Tenant not found")

        conn.commit()
        conn.close()
