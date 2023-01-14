from account_access import AccountAccess
from vault_control import VaultControl
from bitwarden_conn import VaultStatus
import subprocess
import json

class Bitwarden:
    account_access:AccountAccess
    vault_control:VaultControl

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


    def __init__(self) -> None:
        self.account_access = AccountAccess(self)
        self.vault_control = VaultControl(self)
    
    def login(self):
        return self.account_access.login()
    
    def logout(self):
        return self.account_access.logout()

    def lock(self):
        return self.vault_control.lock()

    def unlock(self):
        return self.vault_control.unlock()