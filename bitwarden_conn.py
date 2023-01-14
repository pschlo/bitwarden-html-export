import maskpass
import subprocess
import time
import json
import os
from enum import Enum, auto
from typing import Any, Callable
from login_credentials import *

class VaultStatus(Enum):
    # vault is UNLOCKED iff the environment variable BW_SESSION has been set to a valid session key
    # however, even if BW_SESSION is not set (e.g. state is LOCKED), you can still specify '--session' for every command and access the vault
    # 'bw lock' invalidates the session key. In general, it thus makes sense to run 'bw lock' even when the state is LOCKED
    # But since BitwardenConn always stores the Session Key in the environment variable, this is not relevant
    UNLOCKED = 'unlocked'
    LOCKED = 'locked'
    UNAUTHENTICATED = 'unauthenticated'

class StateChangeError(Exception):
    pass



def askpass():
    pass

def without_first_line(string:str):
    return '\n'.join(string.split('\n')[1:])

class BitwardenConn():

    LOGIN_CALLABLES:dict[LoginMethod,Callable]

    def __init__(self) -> None:
        self.LOGIN_CALLABLES = {
            LoginMethod.EMAIL: self._login_email,
            LoginMethod.API: self._login_api,
            LoginMethod.SSO: self._login_sso
        }
        pass

    # see https://bitwarden.com/help/cli/#status
    @property
    def server_url(self):
        return self.get_bw_status()['serverUrl']

    @property
    def last_sync(self):
        return self.get_bw_status()['lastSync']
    
    @property
    def user_email(self):
        return self.get_bw_status()['userEmail']

    @property
    def user_id(self):
        return self.get_bw_status()['userId']

    @property
    def status(self) -> VaultStatus:
        return VaultStatus(self.get_bw_status()['status'])

    def _run_cmd(self, *args, input=None) -> subprocess.CompletedProcess[str]:
        proc = subprocess.Popen(['./bw', *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(input)
        return subprocess.CompletedProcess(proc.args, proc.returncode, stdout=stdout, stderr=stderr)

    def get_bw_status(self):
        res = self._run_cmd('status')
        status:dict[str,str|None] = json.loads(res.stdout)
        return status


    ## SESSION KEY METHODS

    def get_session_key(self) -> str:
        return os.environ['BW_SESSION']

    # sets session key environment variable
    def set_session_key(self, key:str) -> None:
        os.environ['BW_SESSION'] = key
        if not os.environ['BW_SESSION'] == key:
            raise RuntimeError("Could not set session key")

    # extracts session key from typical bitwarden output
    def extract_session_key(self, input:str) -> str:
        input_splitted:list[str] = input.split()
        if not (input_splitted[-2] == '--session' and input_splitted[-1].endswith('==')):
            raise ValueError("Could not extract session key")
        key = input_splitted[-1]
        self.set_session_key(key)
        return key
    

    ## VAULT STATE CHANGING METHODS

    # afterwards, vault state is UNLOCKED
    def unlock(self, password:str|None=None) -> bool|None:
        status = self.status

        if status == VaultStatus.UNAUTHENTICATED:
            raise StateChangeError("Must authenticate before unlocking vault")

        if status == VaultStatus.UNLOCKED:
            print("Vault is already unlocked")
            return

        assert status == VaultStatus.LOCKED

        if password is not None:
            res = self._run_cmd('unlock', input=password)
            if not (res.returncode == 0 and self.status == VaultStatus.UNLOCKED):
                print(res.stderr)
                return False
            key = self.extract_session_key(res.stdout)
            self.set_session_key(key)
            return True

        # no password provided
        while self.status != VaultStatus.UNLOCKED:
            password = maskpass.askpass("Password [input hidden]: ", mask='')
            res = self._run_cmd('unlock', input=password)
            if res.returncode > 0:
                print(without_first_line(res.stderr))
            else:
                key = self.extract_session_key(res.stdout)
                self.set_session_key(key)


    # logs the user out
    # also verifies that logout was successful
    # afterwards, vault state is UNAUTHENTICATED
    def logout(self) -> None:
        status = self.status

        if status == VaultStatus.UNAUTHENTICATED:
            print("Already logged out")
            return

        if status == VaultStatus.UNLOCKED:
            self.lock()
            print("Locked vault")
            self.logout()
            return

        assert status == VaultStatus.LOCKED

        res = self._run_cmd('logout')
        if not (res.returncode == 0 and self.status == VaultStatus.UNAUTHENTICATED):
            raise StateChangeError("Could not log out")
        print("Logged out")
    
    # afterwards, vault state is LOCKED
    def lock(self) -> None:
        status = self.status

        if status == VaultStatus.UNAUTHENTICATED:
            print("Not authenticated, vaults are locked")
            return
        
        if status == VaultStatus.LOCKED:
            print("Vault is already locked")
            return

        assert status == VaultStatus.UNLOCKED

        res = self._run_cmd('lock')
        if not (res.returncode == 0 and self.status == VaultStatus.LOCKED):
            raise StateChangeError("Could not lock vault")

    # unlock vault
    # user is authenticated if necessary
    # afterwards, vault state is UNLOCKED 
    def login_and_unlock(self, method:LoginMethod=LoginMethod.EMAIL, credentials:LoginCredentials|None=None):
        status = self.status

        if status == VaultStatus.UNLOCKED:
            print("Already authenticated and unlocked")
            return

        if status == VaultStatus.LOCKED:
            print("Already authenticated, but vault is locked")
            print("Unlocking vault")
            self.unlock()
            return

        assert status == VaultStatus.UNAUTHENTICATED

        login_creds:LoginCredentials = METHOD_TO_CREDS[method].ask()

        print("Currently not authenticated, vaults are locked")
        print("Logging in")
        self.login(method, credentials=login_creds)
        print("Unlocking vault")
        # reuse email login password
        password = login_creds.password if method is LoginMethod.EMAIL else None
        self.unlock(password=password)

    # afterwards, vault state is LOCKED
    def login(self, method:LoginMethod=LoginMethod.EMAIL, credentials:LoginCredentials|None=None):
        status = self.status

        if status != VaultStatus.UNAUTHENTICATED:
            print("Already authenticated")
            return

        assert status == VaultStatus.UNAUTHENTICATED

        retval = self.LOGIN_CALLABLES[method](creds=credentials)
        assert self.status == VaultStatus.LOCKED
        print("Successfully authenticated")
        return retval

    # authenticate and unlock vault using email and password
    def _login_email(self, creds:EmailCredentials|None=None):
        if creds:
            res = self._run_cmd('login', creds.email, creds.password, '--method', creds.otp_method, '--code', creds.otp)
            if not (res.returncode == 0 and self.status == VaultStatus.LOCKED):
                print(res.stderr)
                return False
            return True

        # no credentials provided
        while self.status != VaultStatus.LOCKED:
            creds = EmailCredentials.ask()
            res = self._run_cmd('login', creds.email, creds.password, '--method', creds.otp_method, '--code', creds.otp)
            if res.returncode > 0:
                print(res.stderr)
            else:
                # login successful
                # ignore session key so that vault is still locked
                pass

    def _login_api(self, creds:APICredentials|None):
        raise NotImplementedError()
    
    def _login_sso(self, creds:None):
        raise NotImplementedError()
        

#conn = BitwardenConn()
#print(conn.status)
#print(conn.server_url)
#conn.unlock()
#print(conn.login_interactive())