import sqlite3
from datetime import date
from source.app.databases.database import Get_Connection

class ApartmentService:
    @staticmethod
    
    def CreateApartment(
        LocationId: int,
        ApartmentNumber: str,
        ApartmentType: str,
        Rooms: int,
        MonthlyRent: float,
        Status: str = "AVAILABLE"
    ) -> int:
    
        if LocationId <= 0:
            raise ValueError("Invalid location ID.")
        if not ApartmentNumber or not ApartmentNumber.strip():
            raise ValueError("Apartment number is required.")
        if not ApartmentType or not ApartmentType.strip():
            raise ValueError("Apartment type is required.")
        if Rooms <= 0:
            raise ValueError("Rooms must be greater than 0.")
        if MonthlyRent <= 0:
            raise ValueError("Monthly rent must be greater than 0.")
        
        ValidStatuses = ("AVAILABLE", "OCCUPIED", "MAINTENANCE")
        if Status not in ValidStatuses:
            raise ValueError("Invalid apartment status.")
        
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()

            Cursor.execute("""
                INSERT INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (LocationId, ApartmentNumber.strip(), ApartmentType.strip().upper(), Rooms, MonthlyRent, Status))

            ApartmentId = Cursor.lastrowid
            Connection.commit()
            return ApartmentId

        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            Message = str(FailError)

            if "UNIQUE constraint failed" in Message:
                raise ValueError("Apartment already exists in this location.") from FailError
            
            if "FOREIGN KEY constraint failed" in Message:
                raise ValueError("Location does not exist.") from FailError

            raise ValueError("Database integrity error while adding apartment.") from FailError

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    
    @staticmethod
    def GetApartmentById(ApartmentId: int):
        if ApartmentId <= 0:
            raise ValueError("Invalid apartment ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT apartment_id, location_id, apartment_number, type, rooms, monthly_rent, status
                FROM Apartment
                WHERE apartment_id = ?
            """, (ApartmentId,))
            return Cursor.fetchone()

        finally:
            Connection.close()


    @staticmethod
    def GetApartmentsByLocation(LocationId: int):
        if LocationId <= 0:
            raise ValueError("Invalid location ID.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT apartment_id, apartment_number, type, rooms, monthly_rent, status
                FROM Apartment
                WHERE location_id = ?
                ORDER BY apartment_number
            """, (LocationId,))
            return Cursor.fetchall()

        finally:
            Connection.close()

    @staticmethod
    def UpdateApartmentStatus(ApartmentId: int, NewStatus: str):
        if ApartmentId <= 0:
            raise ValueError("ApartmentID cannot be equal or less than 0.")
        ValidStatuses = ("AVAILABLE", "OCCUPIED", "MAINTENANCE")
        if NewStatus not in ValidStatuses:
            raise ValueError("Invalid apartment status.")
        
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            
            Cursor.execute("""
                UPDATE Apartment
                SET status = ?
                WHERE apartment_id = ?
            """, (NewStatus, ApartmentId))

            if Cursor.rowcount == 0:
                raise ValueError("Apartment not found.")
            
            Connection.commit()

        except:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def GetAllApartments():
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT apartment_id, location_id, apartment_number, type, rooms, monthly_rent, status
                FROM Apartment
                ORDER BY location_id, apartment_number
            """)
            return Cursor.fetchall()
        finally:
            Connection.close()
