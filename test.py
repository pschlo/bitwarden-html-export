
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
