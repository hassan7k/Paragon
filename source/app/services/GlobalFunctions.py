import re
NI_REGEX = re.compile(r"^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$") # basically just lets me reuse this so i dont have to re-parse a pattern all the time, needs 6 numbers, ends with a letter A-D, can't start with a certain 2 letters

def Normalise_NI(NI: str) -> str:
    if NI is None:
        raise ValueError("NI number cannot be left blank.")
    NI = NI.strip().upper().replace(" ", "")
    return NI

def ValidateNI(NI: str) -> str:
    NI = Normalise_NI(NI)

    if len(NI) != 9:
        raise ValueError("NI number must be 9 characters, e.g AB123456C")
    if not NI_REGEX.match(NI):
        raise ValueError("Invalid NI format. Expected as in format of AB123456C")
    
    return NI

def ValidatePhone(Number: str) -> str:
    if Number is None:
        raise ValueError("Phone number cannot be left blank.")
    Number = Number.strip().replace(" ", "")

    if Number.startswith("+44") or Number.startswith("0044"):
        raise ValueError("Phone number must start with a 0.")
    if not Number.isdigit():
        raise ValueError("Phone number must contain digits only.")
    if not Number.startswith("0"):
        raise ValueError("Phone number must start with 0.")
    if len(Number) != 11:
        raise ValueError("Phone number must have 11 (eleven) digits in local UK format.")
    
    return Number

def ValidateEmail(Email: str) -> str:
    if Email is None:
        raise ValueError("Email cannot be left blank.")
    Email = Email.strip()
    
    if "@" not in Email or Email.startswith("@") or Email.endswith("@"):
        raise ValueError("Invalid email.")