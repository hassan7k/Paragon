from source.app.services.ApartmentService import ApartmentService


class ApartmentController:

    @staticmethod
    def CreateApartment(*args):
        return ApartmentService.CreateApartment(*args)

    @staticmethod
    def GetApartmentById(apartment_id):
        return ApartmentService.GetApartmentById(apartment_id)

    @staticmethod
    def GetApartmentsByLocation(location_id):
        return ApartmentService.GetApartmentsByLocation(location_id)

    @staticmethod
    def UpdateApartmentStatus(apartment_id, new_status):
        return ApartmentService.UpdateApartmentStatus(apartment_id, new_status)
    
    @staticmethod
    def GetAllApartments():
        return ApartmentService.GetAllApartments()