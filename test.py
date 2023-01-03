import os
import subprocess
from pathlib import Path
import maskpass
import time
import json

import unicodedata
def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")


def get_status():
    args = ['bw', 'status']
    res = subprocess.run(args, capture_output=True, text=True)
    status:dict[str,str|None] = json.loads(res.stdout)
    return status['status']


while True:
    # check if already logged in
    print(get_status())
    exit()

    username = input("username: ")
    password = input("password: ")
    two_step_method = input("2FA method (0: Authenicator, 1: Email, 3: YubiKey OTP): ")
    two_step_key = input("2FA key: ")

    args = ['bw', 'login', username, password, '--method', two_step_method, '--code', two_step_key]
    res = subprocess.run(args, capture_output=True, text=True)

    if res.returncode > 0:
        # error
        print(res.stderr)
        time.sleep(1)
        continue
    
    # login successful, try to extract session key
    stdout_splitted:list[str] = res.stdout.split()
    if not (stdout_splitted[-2] == '--session' and stdout_splitted[-1].endswith('==')):
        raise ValueError("Could not extract session key")

    session_key = stdout_splitted[-1]
    print("Extracted session key:", session_key)
    break



    """
    # this code uses 'bw login' interactively, i.e. sends the username and password on STDIN just like a user would manually

    args = ['bw', 'login', '--method', two_step_method, '--code', two_step_key]
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    assert proc.stdin is not None
    print(proc.stdin.tell())
    proc.stdin.write(username + '\n')
    proc.stdin.flush()
    print(proc.stdin.tell())
    time.sleep(1)
    print(proc.stdin.tell())
    proc.stdin.write(password + '\n')
    proc.stdin.flush()
    time.sleep(1)
    stdout, stderr = proc.communicate()
    print(stdout)
    print(stderr)
    print("return code: ", proc.returncode)
    exit()
    """

# export
args = ['bw', 'export', '--raw', '--format', 'json']
subprocess.run(args, capture_output=True, text=True)
