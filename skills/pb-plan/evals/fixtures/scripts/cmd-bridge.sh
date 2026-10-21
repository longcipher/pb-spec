#!/usr/bin/env python3
"""Bridge: skill-up SessionInput -> Command Code (`cmd -p`) -> SessionResult JSON.

Invoked by skill-up's engine.custom local transport as:
    cmd-bridge.sh <session-input.json> <session-result.json>
"""
import json
import subprocess
import sys
import time

input_path, output_path = sys.argv[1], sys.argv[2]
si = json.load(open(input_path))

workspace = si.get("workspace", ".")
model = si.get("model", "")
# eval.yaml model is provider/name; cmd expects its own provider/name without the
# skill-up engine layer, so strip the leading segment when there are 2+ slashes.
segments = model.split("/")
if len(segments) > 2:
    model = "/".join(segments[1:])

user_msgs = [m for m in si.get("messages", []) if m.get("role") == "user"]
prompt = user_msgs[-1]["content"] if user_msgs else ""

cmd_args = ["cmd", "-p", "--yolo"]
if model:
    cmd_args += ["-m", model]
cmd_args += [prompt]

t0 = time.time()
try:
    proc = subprocess.run(
        cmd_args,
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=si.get("timeout_seconds") or 900,
    )
    exit_code = proc.returncode
    stdout, stderr = proc.stdout, proc.stderr
except subprocess.TimeoutExpired as e:
    exit_code = 124
    stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    stderr = f"bridge timeout after {si.get('timeout_seconds')}s"

final = stdout.strip()
result = {
    "engine": "cmd",
    "model": model,
    "exit_code": exit_code,
    "duration_ms": int((time.time() - t0) * 1000),
    "final_message": final,
    "stderr": stderr.strip()[-4000:],
    "transcript": [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": final},
    ],
}
import os

os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
with open(output_path, "w") as f:
    json.dump(result, f)
json.dump(result, sys.stdout)
