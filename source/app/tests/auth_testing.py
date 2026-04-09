import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.AuthService import AuthService

def ResetDatabase():
    if os.path.exists(DatabasePath):
        os.remove(DatabasePath)

def CreateTempSeed():
    Connection = Get_Connection()
    Cursor = Connection.cursor()

    Cursor.execute("INSERT INTO Location (city) VALUES (?)", ("Bristol",))
    Cursor.execute("SELECT location_id FROM Location WHERE city = ?", ("Bristol",))
    LocationId = Cursor.fetchone()[0]

    Connection.commit()
    Connection.close()

    return LocationId

def Execute():
    print("Running AuthService testing...")

    ResetDatabase()
    Create_Tables()
    LocationId = CreateTempSeed()

    print("All set up.")
    print(f"LocationId={LocationId}")
    print()

    try:
        UserId = AuthService.CreateUser(
            "admin1",
            "SecurePass123",
            "ADMIN",
            LocationId
        )
        print(f"Pass. User created successfully with User ID: {UserId}")

    except Exception as FailError:
        print(f"Fail. Valid user creation raised error: {FailError}")

    try:
        AuthService.CreateUser(
            "admin1",
            "AnotherPass123",
            "ADMIN",
            LocationId
        )
        print("Fail. Should fail due to duplicate username.")

    except Exception as FailError:
        print(f"Pass. Duplicate username failed correctly: {FailError}")

    try:
        AuthService.CreateUser(
            "user2",
            "Password123",
            "BOSS",
            LocationId
        )
        print("Fail. Should fail due to invalid role.")

    except Exception as FailError:
        print(f"Pass. Invalid role failed correctly: {FailError}")

    try:
        UserData = AuthService.Login(
            "admin1",
            "SecurePass123"
        )

        if UserData["role"] == "ADMIN":
            print("Pass. Valid login succeeded.")
        else:
            print("Fail. Login returned incorrect user data.")

    except Exception as FailError:
        print(f"Fail. Valid login raised error: {FailError}")

    try:
        AuthService.Login(
            "admin1",
            "WrongPassword"
        )
        print("Fail. Should fail due to incorrect password.")

    except Exception as FailError:
        print(f"Pass. Invalid password failed correctly: {FailError}")

    try:
        AuthService.Login(
            "ghost",
            "Password123"
        )
        print("Fail. Should fail due to missing user.")

    except Exception as FailError:
        print(f"Pass. Missing user failed correctly: {FailError}")

    try:
        Allowed = AuthService.CheckPermission("ADMIN", ("ADMIN", "MANAGER"))
        Denied = AuthService.CheckPermission("FRONT_DESK", ("ADMIN", "MANAGER"))

        if Allowed and not Denied:
            print("Pass. Permission checking works correctly.")
        else:
            print("Fail. Permission checking returned incorrect results.")

    except Exception as FailError:
        print(f"Fail. Permission checking raised error: {FailError}")

if __name__ == "__main__":
    Execute()
