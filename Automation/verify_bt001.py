# verify_bt001.py

import subprocess

DEVICE_NAME = "Airdopes"

def check_device():
    cmd = 'powershell "Get-PnpDevice | findstr Airdopes"'

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    if DEVICE_NAME.lower() in result.stdout.lower():
        return True

    return False

if check_device():
    print("PASS : Device Connected")
else:
    print("FAIL : Device Not Connected")
