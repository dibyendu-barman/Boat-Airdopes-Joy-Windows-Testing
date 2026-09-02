import subprocess

def is_connected():

    cmd = 'powershell "Get-PnpDevice | findstr Airdopes"'

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    return "Airdopes" in result.stdout


def test_bt_pairing():
    assert is_connected()
``
