import sqlite3
from source.app.services.GlobalFunctions import PasswordFunctions
from source.app.databases.database import Get_Connection

class AuthService:

    @staticmethod
    def CreateUser(Username: str, Password: str, Role: str, LocationId: int) -> bool:
        ValidRoles = ("FRONT_DESK", "FINANCE", "MAINTENANCE", "ADMIN", "MANAGER")
        if not Username or not Username.strip():
            raise ValueError("Username cannot be blank.")
        if not Password or not Password.strip():
            raise ValueError("Password cannot be blank.")
        if Role not in ValidRoles:
            raise ValueError("Role is invalid.")
        if LocationId <= 0:
            raise ValueError("Location Id is invalid.")
        
        PasswordHash = PasswordFunctions.HashPassword(Password)
        
        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                INSERT INTO Users (username, password_hash, role, location_id)
                VALUES (?, ?, ?, ?)
            """, (Username.strip(), PasswordHash, Role, LocationId))
            UserId = Cursor.lastrowid
            Connection.commit()
            return UserId

        except sqlite3.IntegrityError as FailError:
            Connection.rollback()
            Message = str(FailError)

            if "UNIQUE constraint failed: Users.username" in Message:
                raise ValueError("Username already exists.") from FailError
            if "FOREIGN KEY constraint failed" in Message:
                raise ValueError("Location does not exist.") from FailError
            raise ValueError("Database integrity error while creating user.") from FailError

        except Exception:
            Connection.rollback()
            raise

        finally:
            Connection.close()

    @staticmethod
    def Login(Username: str, Password: str):
        if not Username or not Username.strip():
            raise ValueError("Username is blank.")
        if not Password or not Password.strip():
            raise ValueError("Password is blank.")

        User = AuthService.GetUserByUsername(Username)

        if not User:
            raise ValueError("User not found.")

        UserId, StoredUsername, StoredPasswordHash, Role, LocationId = User

        if not PasswordFunctions.VerifyPassword(Password, StoredPasswordHash):
            raise ValueError("Invalid password.")

        return {
            "user_id": UserId,
            "username": StoredUsername,
            "role": Role,
            "location_id": LocationId
        }

    
    @staticmethod
    def GetUserByUsername(Username: str):
        if not Username or not Username.strip():
            raise ValueError("Username is blank.")

        Connection = Get_Connection()
        try:
            Cursor = Connection.cursor()
            Cursor.execute("""
                SELECT user_id, username, password_hash, role, location_id
                FROM Users
                WHERE username = ?
            """, (Username.strip(),))
            return Cursor.fetchone()

        finally:
            Connection.close()

    
    @staticmethod
    def CheckPermission(Role: str, RequiredRoles: tuple) -> bool:
        if not Role or not RequiredRoles:
            return False

        return Role in RequiredRoles