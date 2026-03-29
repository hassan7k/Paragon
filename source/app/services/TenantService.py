import sqlite3
from source.app.databases.database import Get_Connection
from source.app.services.GlobalFunctions import (
    ValidateEmail, ValidateNI, ValidatePhone
)
from source.app.services.LeaseService import LeaseService
from datetime import datetime, timedelta

class TenantService:

    # ---------------- ADD TENANT ----------------
    @staticmethod
    def AddTenant(ni, first, last, phone, email,
                  occupation, reference,
                  requirement, lease_years):

        ni = ValidateNI(ni)
        phone = ValidatePhone(phone)
        email = ValidateEmail(email)

        if not first.strip() or not last.strip():
            raise ValueError("Name required")

        conn = Get_Connection()
        cur = conn.cursor()

        try:
            cur.execute("""
            INSERT INTO Tenant (
                ni_number, first_name, last_name,
                phone, email, occupation, tenant_references,
                apartment_requirement, preferred_lease_years
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ni, first, last, phone, email,
                occupation, reference,
                requirement, lease_years
            ))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError("Tenant already exists")

        finally:
            conn.close()

    # ---------------- GET TENANT ----------------
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
            "tenant_references": row[7],
            "requirement": row[8],
            "lease_years": row[9]
        }

    # ---------------- SEARCH ----------------
    @staticmethod
    def Search(keyword=""):
        conn = Get_Connection()
        cur = conn.cursor()

        query = """
        SELECT tenant_id, ni_number, first_name, last_name, phone, email, occupation
        FROM Tenant
        WHERE ni_number LIKE ? OR first_name LIKE ? OR last_name LIKE ?
        """

        k = f"%{keyword}%"
        cur.execute(query, (k, k, k))

        data = cur.fetchall()
        conn.close()
        return data

    # ---------------- UPDATE ----------------
    @staticmethod
    def UpdateTenant(ni, first, last, phone, email,
                     occupation, reference, requirement, lease_years):

        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        UPDATE Tenant
        SET first_name=?, last_name=?, phone=?, email=?,
            occupation=?, tenant_references=?,
            apartment_requirement=?, preferred_lease_years=?
        WHERE ni_number=?
        """, (
            first, last, phone, email,
            occupation, reference,
            requirement, lease_years, ni
        ))

        conn.commit()
        conn.close()

    # ---------------- DELETE ----------------
    @staticmethod
    def DeleteTenant(ni):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM Tenant WHERE ni_number=?", (ni,))
        conn.commit()
        conn.close()

    # ---------------- COMPLAINT ----------------
    @staticmethod
    def AddComplaint(ni, desc):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("SELECT tenant_id FROM Tenant WHERE ni_number=?", (ni,))
        t = cur.fetchone()

        if not t:
            raise ValueError("Tenant not found")

        cur.execute("""
        INSERT INTO Complaint (tenant_id, description)
        VALUES (?, ?)
        """, (t[0], desc))

        conn.commit()
        conn.close()

    @staticmethod
    def GetComplaints():
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT t.first_name, c.description, c.status
        FROM Complaint c
        JOIN Tenant t ON c.tenant_id = t.tenant_id
        """)

        data = cur.fetchall()
        conn.close()
        return data

    # ---------------- MAINTENANCE ----------------
    @staticmethod
    def AddMaintenance(ni, apartment_id, desc):
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("SELECT tenant_id FROM Tenant WHERE ni_number=?", (ni,))
        t = cur.fetchone()

        if not t:
            raise ValueError("Tenant not found")

        cur.execute("""
        INSERT INTO MaintenanceRequest (tenant_id, apartment_id, description, priority)
        VALUES (?, ?, ?, 'MEDIUM')
        """, (t[0], apartment_id, desc))

        conn.commit()
        conn.close()

    @staticmethod
    def GetMaintenance():
        conn = Get_Connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT t.first_name, m.apartment_id, m.description, m.status
        FROM MaintenanceRequest m
        JOIN Tenant t ON m.tenant_id = t.tenant_id
        """)

        data = cur.fetchall()
        conn.close()
        return data