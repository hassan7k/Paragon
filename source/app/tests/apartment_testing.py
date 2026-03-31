import os
from source.app.databases.database import DatabasePath, Create_Tables, Get_Connection
from source.app.services.ApartmentService import ApartmentService

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
    print("Running ApartmentService testing...")

    ResetDatabase()
    Create_Tables()
    LocationId = CreateTempSeed()

    print("All set up.")
    print(f"LocationId={LocationId}")
    print()

    # Test 1: Valid apartment creation
    try:
        AptId = ApartmentService.CreateApartment(LocationId, "A101", "FLAT", 2, 1200.0)
        print(f"Pass. Apartment created with ID: {AptId}")
    except Exception as FailError:
        print(f"Fail. Valid apartment creation raised error: {FailError}")

    # Test 2: Duplicate apartment number in same location
    try:
        ApartmentService.CreateApartment(LocationId, "A101", "FLAT", 2, 1200.0)
        print("Fail. Should fail due to duplicate apartment number.")
    except Exception as FailError:
        print(f"Pass. Duplicate apartment failed correctly: {FailError}")

    # Test 3: Invalid location
    try:
        ApartmentService.CreateApartment(9999, "B101", "FLAT", 2, 1200.0)
        print("Fail. Should fail due to invalid location.")
    except Exception as FailError:
        print(f"Pass. Invalid location failed correctly: {FailError}")

    # Test 4: Get apartment by ID
    try:
        Apt = ApartmentService.GetApartmentById(AptId)
        if Apt and Apt[2] == "A101":
            print("Pass. GetApartmentById returned correct data.")
        else:
            print("Fail. GetApartmentById returned wrong data.")
    except Exception as FailError:
        print(f"Fail. GetApartmentById raised error: {FailError}")

    # Test 5: Update status
    try:
        ApartmentService.UpdateApartmentStatus(AptId, "MAINTENANCE")
        Apt = ApartmentService.GetApartmentById(AptId)
        if Apt[6] == "MAINTENANCE":
            print("Pass. Apartment status updated to MAINTENANCE.")
        else:
            print("Fail. Status not updated correctly.")
    except Exception as FailError:
        print(f"Fail. Status update raised error: {FailError}")

if __name__ == "__main__":
    Execute()
