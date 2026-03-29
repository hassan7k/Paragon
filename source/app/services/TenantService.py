import sqlite3
from source.app.databases.database import Get_Connection
from source.app.services.GlobalFunctions import (
    ValidateEmail, ValidateNI, ValidatePhone
)


class TenantService:

    # ---------------- ADD TENANT ----------------
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

        # Clean + validate
        NI_number = ValidateNI(NI_number.strip())
        Phone = ValidatePhone(Phone.strip())
        Email = ValidateEmail(Email.strip())
        FirstName = FirstName.strip()
        LastName = LastName.strip()

        if not FirstName:
            raise ValueError("First name is required.")
        if not LastName:
            raise ValueError("Last name is required.")

        conn = Get_Connection()

        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO Tenant 
                (ni_number, first_name, last_name, phone, email, occupation, tenant_references)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                NI_number,
                FirstName,
                LastName,
                Phone,
                Email,
                Occupation,
                TenantReference
            ))

            tenant_id = cur.lastrowid
            conn.commit()
            return tenant_id

        except sqlite3.IntegrityError as e:
            conn.rollback()

            if "ni_number" in str(e).lower():
                raise ValueError("Tenant with this NI already exists.")

            raise ValueError("Database integrity error.")

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Unexpected error: {e}")

        finally:
            conn.close()

    # ---------------- UPDATE TENANT ----------------
    @staticmethod
    def UpdateTenant(
        NI_number: str,
        FirstName: str,
        LastName: str,
        Phone: str,
        Email: str,
        Occupation: str | None = None,
        TenantReference: str | None = None
    ) -> None:

        NI_number = ValidateNI(NI_number.strip())
        Phone = ValidatePhone(Phone.strip())
        Email = ValidateEmail(Email.strip())
        FirstName = FirstName.strip()
        LastName = LastName.strip()

        if not FirstName:
            raise ValueError("First name is required.")
        if not LastName:
            raise ValueError("Last name is required.")

        conn = Get_Connection()

        try:
            cur = conn.cursor()

            # Check exists
            cur.execute("SELECT tenant_id FROM Tenant WHERE ni_number=?", (NI_number,))
            if not cur.fetchone():
                raise ValueError("Tenant not found.")

            cur.execute("""
                UPDATE Tenant
                SET first_name=?, last_name=?, phone=?, email=?, occupation=?, tenant_references=?
                WHERE ni_number=?
            """, (
                FirstName,
                LastName,
                Phone,
                Email,
                Occupation,
                TenantReference,
                NI_number
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Update failed: {e}")

        finally:
            conn.close()

    # ---------------- SEARCH TENANT ----------------
    @staticmethod
    def SearchTenants(keyword: str = "", occupation: str = ""):
        conn = Get_Connection()

        try:
            cur = conn.cursor()

            query = """
            SELECT tenant_id, ni_number, first_name, last_name, phone, email, occupation
            FROM Tenant
            WHERE 1=1
            """
            params = []

            if keyword:
                query += """
                AND (
                    ni_number LIKE ?
                    OR first_name LIKE ?
                    OR last_name LIKE ?
                    OR email LIKE ?
                )
                """
                k = f"%{keyword}%"
                params.extend([k, k, k, k])

            if occupation:
                query += " AND occupation LIKE ?"
                params.append(f"%{occupation}%")

            cur.execute(query, params)
            return cur.fetchall()

        finally:
            conn.close()
            
    # ---------------- DELETE TENANT ----------------
    @staticmethod
    def DeleteTenant(NI_number: str) -> None:

        NI_number = ValidateNI(NI_number.strip())

        conn = Get_Connection()

        try:
            cur = conn.cursor()

            cur.execute("SELECT tenant_id FROM Tenant WHERE ni_number=?", (NI_number,))
            tenant = cur.fetchone()

            if not tenant:
                raise ValueError("Tenant not found.")

            tenant_id = tenant[0]

            # Prevent deleting if active lease exists
            cur.execute("""
                SELECT lease_id FROM Lease 
                WHERE tenant_id=? AND status='ACTIVE'
            """, (tenant_id,))

            if cur.fetchone():
                raise ValueError("Cannot delete tenant with active lease.")

            cur.execute("DELETE FROM Tenant WHERE tenant_id=?", (tenant_id,))
            conn.commit()

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Delete failed: {e}")

        finally:
            conn.close()

    # ---------------- GET SINGLE TENANT ----------------
    @staticmethod
    def GetTenant(NI_number: str):

        NI_number = ValidateNI(NI_number.strip())

        conn = Get_Connection()

        try:
            cur = conn.cursor()

            cur.execute("SELECT * FROM Tenant WHERE ni_number=?", (NI_number,))
            t = cur.fetchone()

            if not t:
                return None

            return {
                "tenant_id": t[0],
                "ni_number": t[1],
                "first_name": t[2],
                "last_name": t[3],
                "phone": t[4],
                "email": t[5],
                "occupation": t[6],
                "tenant_references": t[7]
            }

        finally:
            conn.close()

    # ---------------- GET ALL TENANTS ----------------
    @staticmethod
    def GetAllTenants():

        conn = Get_Connection()

        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Tenant")
            return cur.fetchall()

        finally:
            conn.close()

    # ---------------- ADD COMPLAINT ----------------
    @staticmethod
    def AddComplaint(NI_number: str, description: str):

        if not description.strip():
            raise ValueError("Complaint cannot be empty.")

        NI_number = ValidateNI(NI_number.strip())

        conn = Get_Connection()

        try:
            cur = conn.cursor()

            cur.execute("SELECT tenant_id FROM Tenant WHERE ni_number=?", (NI_number,))
            tenant = cur.fetchone()

            if not tenant:
                raise ValueError("Tenant not found.")

            tenant_id = tenant[0]

            cur.execute("""
                INSERT INTO Complaint (tenant_id, description)
                VALUES (?, ?)
            """, (tenant_id, description))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to add complaint: {e}")

        finally:
            conn.close()

    # ---------------- REPORTS (HIGH MARK FEATURE) ----------------
    @staticmethod
    def CountTenants():
        conn = Get_Connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Tenant")
            return cur.fetchone()[0]
        finally:
            conn.close()

    @staticmethod
    def CountComplaints():
        conn = Get_Connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Complaint")
            return cur.fetchone()[0]
        finally:
            conn.close()