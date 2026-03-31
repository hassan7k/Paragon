from source.app.services.ApartmentService import ApartmentService

class Apartments:
    
    @staticmethod
    def CreateApartment(LocationId: int, ApartmentNumber: str, ApartmentType: str, Rooms: int, MonthlyRent: float, Status: str = "AVAILABLE"):
        return ApartmentService.CreateApartment(LocationId, ApartmentNumber, ApartmentType, Rooms, MonthlyRent, Status)
    
    @staticmethod
    def GetApartmentById():
        pass