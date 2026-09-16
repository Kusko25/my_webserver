import json
import subprocess
from pathlib import Path


class ToolInvocationError(Exception):
    pass

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

def call_external_tool(name, params=[], parseAsJson=False) -> bytes | dict:
    path = Path(__file__).parent / "external_tools" / name
    if not path.exists():
        raise FileNotFoundError(f"External tool '{name}' not found.")
    output = subprocess.run([str(path), *params], capture_output=True,check=True)
    if parseAsJson:
        return json.loads(output.stdout)
    else:
        return output.stdout

def monitor_toggle(monitor:int=2):
    call_external_tool('MultiMonitorTool.exe', ['/SwitchOffOn', str(monitor)])