from enum import Enum, auto
import maskpass


class OTPMethod(Enum):
    AUTHENTICATOR = 0
    EMAIL = 1
    YUBIKEY = 3


class LoginCredentials:
    pass


class EmailCredentials(LoginCredentials):
    email:str
    password:str
    otp:str|None
    otp_method:OTPMethod|None

    def __init__(self, email:str, password:str, otp:str|None=None, otp_method:OTPMethod|None=None) -> None:
        self.email = email
        self.password = password

        if otp and not otp_method:
            raise ValueError("Must provide OTP method")
        if otp_method and not otp:
            raise ValueError("Must provide OTP")
        self.otp = otp
        self.otp_method = otp_method


    @staticmethod
    def ask():
        print()
        email = input("Email: ")
        password = maskpass.askpass("Password [input hidden]: ", mask='')
        otp_method = OTPMethod(int(input("2FA method (0: Authenicator, 1: Email, 3: YubiKey OTP): ")))
        otp = input("2FA key: ")
        print()
        
        return EmailCredentials(email, password, otp, otp_method)

class APICredentials(LoginCredentials):
    pass

class SSOCredentials(LoginCredentials):
    pass










METHOD_TO_CREDS:dict[LoginMethod, LoginCredentials] = {
    LoginMethod.EMAIL: EmailCredentials,
    LoginMethod.API: APICredentials,
    LoginMethod.SSO: SSOCredentials
}