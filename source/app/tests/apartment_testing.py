import os
from source.app.databases.Database import DatabasePath, Create_Tables, Get_Connection
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

    ApartmentId = None

    try:
        ApartmentId = ApartmentService.CreateApartment(
            LocationId,
            "A101",
            "FLAT",
            2,
            1200.0,
            "AVAILABLE"
        )
        print(f"Pass. Valid apartment inserted with Apartment ID: {ApartmentId}")

    except Exception as FailError:
        print(f"Fail. Valid apartment insert raised error: {FailError}")

    try:
        ApartmentService.CreateApartment(
            LocationId,
            "A101",
            "FLAT",
            2,
            1200.0,
            "AVAILABLE"
        )
        print("Fail. Should fail due to duplicate apartment in same location.")

    except Exception as FailError:
        print(f"Pass. Duplicate apartment failed correctly: {FailError}")

    try:
        ApartmentService.CreateApartment(
            999999,
            "A102",
            "FLAT",
            2,
            1200.0,
            "AVAILABLE"
        )
        print("Fail. Should fail due to invalid location ID.")

    except Exception as FailError:
        print(f"Pass. Invalid location ID failed correctly: {FailError}")

    try:
        ApartmentService.CreateApartment(
            LocationId,
            "A103",
            "FLAT",
            0,
            1200.0,
            "AVAILABLE"
        )
        print("Fail. Should fail due to invalid room count.")

    except Exception as FailError:
        print(f"Pass. Invalid room count failed correctly: {FailError}")

    try:
        ApartmentService.CreateApartment(
            LocationId,
            "A104",
            "FLAT",
            2,
            -100.0,
            "AVAILABLE"
        )
        print("Fail. Should fail due to invalid monthly rent.")

    except Exception as FailError:
        print(f"Pass. Invalid monthly rent failed correctly: {FailError}")

    try:
        ApartmentService.CreateApartment(
            LocationId,
            "A105",
            "FLAT",
            2,
            1200.0,
            "BROKEN"
        )
        print("Fail. Should fail due to invalid status.")

    except Exception as FailError:
        print(f"Pass. Invalid status failed correctly: {FailError}")

    try:
        if ApartmentId is not None:
            ApartmentService.UpdateApartmentStatus(ApartmentId, "MAINTENANCE")
            ApartmentData = ApartmentService.GetApartmentById(ApartmentId)

            if ApartmentData and ApartmentData[6] == "MAINTENANCE":
                print("Pass. Apartment status updated correctly.")
            else:
                print(f"Fail. Apartment status should be MAINTENANCE, got {ApartmentData[6]} instead.")
        else:
            print("Skipped. Update apartment status test could not run.")

    except Exception as FailError:
        print(f"Fail. Updating apartment status raised error: {FailError}")

    try:
        if ApartmentId is not None:
            ApartmentData = ApartmentService.GetApartmentById(ApartmentId)

            if ApartmentData and ApartmentData[0] == ApartmentId:
                print("Pass. Apartment retrieved by ID correctly.")
            else:
                print("Fail. Apartment retrieval by ID returned incorrect data.")
        else:
            print("Skipped. Get apartment by ID test could not run.")

    except Exception as FailError:
        print(f"Fail. Getting apartment by ID raised error: {FailError}")

    try:
        Apartments = ApartmentService.GetApartmentsByLocation(LocationId)

        if len(Apartments) >= 1:
            print(f"Pass. Apartments retrieved by location correctly. Count: {len(Apartments)}")
        else:
            print("Fail. Expected at least one apartment for this location.")

    except Exception as FailError:
        print(f"Fail. Getting apartments by location raised error: {FailError}")

if __name__ == "__main__":
    Execute()