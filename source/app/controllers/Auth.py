from source.app.services.AuthService import AuthService


class AuthController:

    @staticmethod
    def Login(Username: str, Password: str):
        return AuthService.Login(Username, Password)

    @staticmethod
    def CreateUser(Username: str, Password: str, Role: str, LocationId: int):
        return AuthService.CreateUser(Username, Password, Role, LocationId)