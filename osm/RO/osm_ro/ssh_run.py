import paramiko
import socket

def ssh_run(ip, user, cmd, password=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if password is not None:
            ssh.connect(hostname=ip, username=user, password=password, compress=True,look_for_keys=False)
        else:
            ssh.connect(hostname=ip, username=user, compress=True, look_for_keys=True)
    except (socket.error,paramiko.AuthenticationException,paramiko.SSHException) as message:
        return "ERROR: SSH connection to " + ip + " failed: " + str(message)

    stdin, stdout, ssh_stderr = ssh.exec_command(cmd)
    out = stdout.read()
    stdin.flush()
    ssh.close()
    return out
