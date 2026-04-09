from source.app.databases.database import Get_Connection
from source.app.services.GlobalFunctions import PasswordFunctions


def SeedDatabase():
    """Insert default locations, admin accounts and sample apartments."""
    Connection = Get_Connection()
    Cursor = Connection.cursor()

    # ── Locations ────────────────────────────────────────
    Cities = ["Bristol", "Cardiff", "London", "Manchester"]
    for City in Cities:
        Cursor.execute("INSERT OR IGNORE INTO Location (city) VALUES (?)", (City,))

    # Fetch location IDs
    Cursor.execute("SELECT location_id, city FROM Location ORDER BY location_id")
    Locations = {row[1]: row[0] for row in Cursor.fetchall()}

    # ── Default Users ────────────────────────────────────
    DefaultUsers = [
        ("manager",  "Manager123",  "MANAGER",     Locations["Bristol"]),
        ("admin1",   "Admin123",    "ADMIN",        Locations["Bristol"]),
        ("admin2",   "Admin123",    "ADMIN",        Locations["Cardiff"]),
        ("front1",   "Front123",    "FRONT_DESK",   Locations["Bristol"]),
        ("finance1", "Finance123",  "FINANCE",      Locations["Bristol"]),
        ("maint1",   "Maint123",    "MAINTENANCE",  Locations["Bristol"]),
    ]
    for Username, Password, Role, LocId in DefaultUsers:
        Cursor.execute("SELECT 1 FROM Users WHERE username = ?", (Username,))
        if not Cursor.fetchone():
            PasswordHash = PasswordFunctions.HashPassword(Password)
            Cursor.execute("""
                INSERT INTO Users (username, password_hash, role, location_id)
                VALUES (?, ?, ?, ?)
            """, (Username, PasswordHash, Role, LocId))

    # ── Sample Apartments ────────────────────────────────
    SampleApartments = [
        (Locations["Bristol"],     "A101", "FLAT",   2, 1200.00),
        (Locations["Bristol"],     "A102", "FLAT",   1,  950.00),
        (Locations["Bristol"],     "B201", "STUDIO", 1,  750.00),
        (Locations["Cardiff"],     "C101", "FLAT",   3, 1400.00),
        (Locations["Cardiff"],     "C102", "FLAT",   2, 1100.00),
        (Locations["London"],      "L101", "FLAT",   2, 1800.00),
        (Locations["London"],      "L102", "STUDIO", 1, 1300.00),
        (Locations["Manchester"],  "M101", "FLAT",   2, 1000.00),
    ]
    for LocId, Number, Type, Rooms, Rent in SampleApartments:
        Cursor.execute(
            "SELECT 1 FROM Apartment WHERE location_id = ? AND apartment_number = ?",
            (LocId, Number)
        )
        if not Cursor.fetchone():
            Cursor.execute("""
                INSERT INTO Apartment (location_id, apartment_number, type, rooms, monthly_rent, status)
                VALUES (?, ?, ?, ?, ?, 'AVAILABLE')
            """, (LocId, Number, Type, Rooms, Rent))

    Connection.commit()
    Connection.close()
    print("Seed data inserted successfully.")
