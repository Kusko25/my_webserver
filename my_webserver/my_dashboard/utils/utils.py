import subprocess
import json
from pathlib import Path

def process_show_name(show_name):
    processed_show_name = ""
    show_name = show_name.strip()
    # Cast to title case but preserve uppercase letters
    for i,c in enumerate(show_name.title()):
        if show_name[i].isupper():
            processed_show_name += show_name[i]
        else:
            processed_show_name += c

    return processed_show_name

def call_external_tool(name, params=[], parseAsJson=False):
    path = Path(__file__).parent / "external_tools" / name
    if not path.exists():
        raise FileNotFoundError(f"External tool '{name}' not found.")
    output = subprocess.run([str(path), *params], capture_output=True)
    if output.returncode != 0:
        raise Exception(f"External tool '{name}' failed with error code {output.returncode}:\n{output.stderr}")
    if parseAsJson:
        return json.loads(output.stdout)
    else:
        return output.stdout

def monitor_toggle(monitor:int=2):
    call_external_tool('MultiMonitorTool.exe', ['/SwitchOffOn', str(monitor)])