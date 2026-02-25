import sqlite3
from app.databases.Database import Get_Connection
from source.app.services.GlobalFunctions import (
    ValidateEmail, ValidateNI, ValidatePhone
)

class TenantService:

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
            raise ValueError("Tenant already exists - duplicate NI") from FailError
        
        except Exception:
            Connection.rollback()
        
        finally:
            Connection.close()
