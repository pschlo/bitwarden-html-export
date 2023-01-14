from bitwarden import Bitwarden
from bitwarden_conn import VaultStatus
import os
import maskpass

class VaultControl:
    bw:Bitwarden

    def __init__(self, bw:Bitwarden) -> None:
        self.bw = bw


    # afterwards, vault state is UNLOCKED
    def unlock(self, password:str|None=None) -> bool|None:
        status = self.bw.status

        if status == VaultStatus.UNAUTHENTICATED:
            raise StateChangeError("Must authenticate before unlocking vault")

        if status == VaultStatus.UNLOCKED:
            print("Vault is already unlocked")
            return

        assert status == VaultStatus.LOCKED

        if password is not None:
            res = self.bw._run_cmd('unlock', input=password)
            if not (res.returncode == 0 and self.bw.status == VaultStatus.UNLOCKED):
                print(res.stderr)
                return False
            key = self.extract_session_key(res.stdout)
            self.set_session_key(key)
            return True

        # no password provided
        while self.bw.status != VaultStatus.UNLOCKED:
            password = maskpass.askpass("Password [input hidden]: ", mask='')
            res = self.bw._run_cmd('unlock', input=password)
            if res.returncode > 0:
                print(without_first_line(res.stderr))
            else:
                key = self.extract_session_key(res.stdout)
                self.set_session_key(key)


    
    # afterwards, vault state is LOCKED
    def lock(self) -> None:
        status = self.bw.status

        if status == VaultStatus.UNAUTHENTICATED:
            print("Not authenticated, vaults are locked")
            return
        
        if status == VaultStatus.LOCKED:
            print("Vault is already locked")
            return

        assert status == VaultStatus.UNLOCKED

        res = self.bw._run_cmd('lock')
        if not (res.returncode == 0 and self.bw.status == VaultStatus.LOCKED):
            raise StateChangeError("Could not lock vault")

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