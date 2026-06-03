# apsim_server.py

import subprocess
import socket
import os
from pathlib import Path
from apsimNGpy.core.config import get_apsim_bin_path
import platform

HOST = "127.0.0.1"
PORT = 5055


def apsim_command():
    system = platform.system()
    if system == "Windows":
        return [os.path.realpath(Path(get_apsim_bin_path()) / 'Models.exe'), ]
    else:
        return ["dotnet", os.path.realpath(Path(get_apsim_bin_path()) / 'Models.dll'), "--mode:server"]


def start_engine():
    return subprocess.Popen(
        apsim_command(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )


def main():
    engine = start_engine()
    print("APSIM engine ready...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, _ = s.accept()
            with conn:
                path = conn.recv(4096).decode().strip()

                # 🟢 Correct APSIM 2025.x command protocol:
                engine.stdin.write(f"load {path}\n")
                engine.stdin.write("run\n")
                engine.stdin.write("status\n")
                engine.stdin.flush()

                # APSIM prints version first
                version = engine.stdout.readline().strip()

                # Then status of run (success/error)
                status = engine.stdout.readline().strip()

                conn.send(status.encode())


if __name__ == "__main__":
    main()
