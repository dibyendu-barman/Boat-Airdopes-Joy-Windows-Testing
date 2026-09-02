import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

DEVICE_KEYWORD = "Airdopes"
DISCONNECT_TIMEOUT_SECONDS = 45
RECONNECT_TIMEOUT_SECONDS = 60
POLL_INTERVAL_SECONDS = 3

REPORT_DIRECTORY = Path("Reports")
REPORT_FILE = REPORT_DIRECTORY / "BT_002_Auto_Reconnect_Report.md"


def get_matching_devices():
    """
    Return Windows PnP devices whose friendly name contains DEVICE_KEYWORD.
    """

    escaped_keyword = DEVICE_KEYWORD.replace("'", "''")

    powershell_command = f"""
    $devices = Get-PnpDevice -PresentOnly |
        Where-Object {{
            $_.FriendlyName -and
            $_.FriendlyName -like '*{escaped_keyword}*'
        }} |
        Select-Object Status, Class, FriendlyName, InstanceId

    @($devices) | ConvertTo-Json -Compress
    """

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            powershell_command,
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"PowerShell command failed: {result.stderr.strip()}"
        )

    output = result.stdout.strip()

    if not output:
        return []

    parsed_output = json.loads(output)

    if isinstance(parsed_output, dict):
        return [parsed_output]

    return parsed_output


def is_airdopes_available():
    """
    Return True when at least one matching present device has Status OK.
    """

    devices = get_matching_devices()

    return any(
        device.get("Status", "").upper() == "OK"
        for device in devices
    )


def wait_for_state(expected_state, timeout_seconds):
    """
    Poll the Windows device state until it matches expected_state.
    """

    start_time = time.monotonic()

    while time.monotonic() - start_time < timeout_seconds:
        current_state = is_airdopes_available()

        if current_state == expected_state:
            return True

        time.sleep(POLL_INTERVAL_SECONDS)

    return False


def write_report(status, details):
    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    report = f"""# BT_002 Auto-Reconnection Test Report

## Execution Information

- **Execution time:** {datetime.now().isoformat(timespec="seconds")}
- **Operating system:** Windows 10
- **Device keyword:** {DEVICE_KEYWORD}
- **Test status:** {status}

## Test Details

{details}
"""

    REPORT_FILE.write_text(report, encoding="utf-8")


def test_bt002_auto_reconnect():
    if not is_airdopes_available():
        pytest_message = (
            "Precondition failed: Airdopes was not detected with status OK. "
            "Pair and connect the earbuds before starting the test."
        )
        write_report("BLOCKED", pytest_message)
        raise AssertionError(pytest_message)

    print("\nBT_002 Auto-Reconnection Test")
    print("The Airdopes is currently detected.")
    print("Switch OFF the earbuds now.")

    disconnected = wait_for_state(
        expected_state=False,
        timeout_seconds=DISCONNECT_TIMEOUT_SECONDS,
    )

    if not disconnected:
        message = (
            "FAIL: Windows did not detect the expected disconnection "
            f"within {DISCONNECT_TIMEOUT_SECONDS} seconds."
        )
        write_report("FAIL", message)
        raise AssertionError(message)

    print("Disconnection detected.")
    print("Switch ON the earbuds now. Do not pair them again manually.")

    reconnect_start = time.monotonic()

    reconnected = wait_for_state(
        expected_state=True,
        timeout_seconds=RECONNECT_TIMEOUT_SECONDS,
    )

    reconnect_duration = time.monotonic() - reconnect_start

    if not reconnected:
        message = (
            "FAIL: Airdopes did not automatically reconnect "
            f"within {RECONNECT_TIMEOUT_SECONDS} seconds."
        )
        write_report("FAIL", message)
        raise AssertionError(message)

    message = (
        "PASS: Airdopes automatically reappeared with status OK. "
        f"Observed reconnection time: {reconnect_duration:.1f} seconds."
    )

    write_report("PASS", message)
    print(message)
