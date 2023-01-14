from enum import Enum, auto
from bitwarden import Bitwarden
from bitwarden_conn import VaultStatus
from login_credentials import *


class LoginMethod(Enum):
    EMAIL = auto()
    API = auto()
    SSO = auto()


class AccountAccess:
    bw:Bitwarden

    def __init__(self, bw_conn:Bitwarden) -> None:
        self.bw = bw_conn

    # afterwards, vault state is LOCKED
    def login(self, method:LoginMethod=LoginMethod.EMAIL, credentials:LoginCredentials|None=None):
        status = self.bw.status

        if status != VaultStatus.UNAUTHENTICATED:
            print("Already authenticated")
            return

        assert status == VaultStatus.UNAUTHENTICATED

        retval = self.LOGIN_CALLABLES[method](creds=credentials)
        assert self.bw.status == VaultStatus.LOCKED
        print("Successfully authenticated")
        return retval

    # logs the user out
    # also verifies that logout was successful
    # afterwards, vault state is UNAUTHENTICATED
    def logout(self) -> None:
        status = self.bw.status

        if status == VaultStatus.UNAUTHENTICATED:
            print("Already logged out")
            return

        if status == VaultStatus.UNLOCKED:
            self.bw.lock()
            print("Locked vault")
            self.logout()
            return

        assert status == VaultStatus.LOCKED

        res = self.bw._run_cmd('logout')
        if not (res.returncode == 0 and self.bw.status == VaultStatus.UNAUTHENTICATED):
            raise StateChangeError("Could not log out")
        print("Logged out")


class EmailAccess(AccountAccess):
    def __init__(self, bw_conn: Bitwarden) -> None:
        super().__init__(bw_conn)

    # authenticate and unlock vault using email and password
    def login(self, creds:EmailCredentials|None=None):
        if creds:
            res = self.bw._run_cmd('login', creds.email, creds.password, '--method', creds.otp_method, '--code', creds.otp)
            if not (res.returncode == 0 and self.bw.status == VaultStatus.LOCKED):
                print(res.stderr)
                return False
            return True

        # no credentials provided
        while self.bw.status != VaultStatus.LOCKED:
            creds = EmailCredentials.ask()
            res = self.bw._run_cmd('login', creds.email, creds.password, '--method', creds.otp_method, '--code', creds.otp)
            if res.returncode > 0:
                print(res.stderr)
            else:
                # login successful
                # ignore session key so that vault is still locked
                pass


class APIAccess(AccountAccess):
    def login(self, creds:APICredentials|None):
        raise NotImplementedError()
    
class SSOAccess(AccountAccess):
    def login(self, creds:None):
        raise NotImplementedError()