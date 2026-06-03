import platform
import socket
import struct
import subprocess
from ctypes import c_int32, c_double, c_char
from pathlib import Path

import pandas as pd


class ApsimProtocolError(RuntimeError):
    pass


ACK = 'ACK'
FIN = 'FIN'
COMMAND_RUN = 'RUN'
COMMAND_READ = 'READ'

PROPERTY_TYPE_INT = 0
PROPERTY_TYPE_DOUBLE = 1
PROPERTY_TYPE_STRING = 4
from apsimNGpy import configuration, logger


def send_bytes(sock, payload: bytes):
    sock.sendall(struct.pack('!I', len(payload)))
    sock.sendall(payload)


def send_string(sock, value: str):
    payload = value.encode('utf-8')
    send_bytes(sock, payload)


def send_int(sock, value: int):
    payload = struct.pack('!i', value)
    send_bytes(sock, payload)


def send_double(sock, value: float):
    payload = struct.pack('!d', value)
    send_bytes(sock, payload)


def read_int(sock: socket.socket) -> int:
    return struct.unpack('!I', _recv_exact(sock, 4))[0]


def read_bytes(sock: socket.socket) -> bytes:
    length = read_int(sock)
    return _recv_exact(sock, length)


def read_string(sock: socket.socket) -> str:
    return read_bytes(sock).decode('utf-8')


def read_from_socket(sock):
    size = read_int(sock)
    data = _recv_exact(sock, size)
    return size, data


def validate_response(sock, expected: str):
    _, data = read_from_socket(sock)
    resp = data.decode()
    if resp != expected:
        raise ApsimProtocolError(f"Expected '{expected}', got '{resp}'")


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("Socket closed while receiving data")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


# ---------------------------
# CONNECTION
# ---------------------------
def connect_to_remote_server(ip_address, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip_address, port))
    return client


def disconnect_from_server(sock):
    sock.close()


# ---------------------------
# SOCKET UTILITIES
# ---------------------------
def recv_all(sock, size):
    """Ensure full read from socket"""
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            raise ConnectionError("Socket connection lost")
        data += packet
    return data


def send_to_socket(sock, msg):
    if isinstance(msg, int):
        payload = struct.pack('<i', msg)
    elif isinstance(msg, float):
        payload = struct.pack('<d', msg)
    elif isinstance(msg, str):
        encoded = msg.encode()
        payload = struct.pack(f'<{len(encoded)}s', encoded)
    else:
        raise TypeError(f"Unsupported type: {type(msg)}")

    sock.send(struct.pack('<i', len(payload)))  # length
    sock.send(payload)


# def read_from_socket(sock):
#     header = recv_all(sock, 4)
#     su = struct.unpack('<i', header)
#     print(su)
#     size = su[0]
#     data = recv_all(sock, size)
#     print('data', data)
#     return size, data




# ---------------------------
# SEND HELPERS
# ---------------------------



# ---------------------------
# PARAM CHANGE
# ---------------------------
def send_replacement(sock, change):
    # 1. path
    send_string(sock, change["path"])
    validate_response(sock, ACK)

    # 2. type
    send_int(sock, change["paramtype"])
    validate_response(sock, ACK)

    # 3. value
    value = change["value"]
    if isinstance(value, float):
        send_double(sock, value)
    elif isinstance(value, int):
        send_int(sock, value)
    elif isinstance(value, str):
        send_string(sock, value)
    else:
        raise TypeError("Unsupported value type")

    validate_response(sock, ACK)


def wait_for_fin(sock):
    while True:
        _, data = read_from_socket(sock)
        resp = data.decode()

        if resp == FIN:
            return
        elif resp == ACK:
            continue  # ignore extra ACKs
        else:
            print(f"⚠️ Unexpected response: {resp}")


# ---------------------------
# RUN
# ---------------------------
def run_with_changes(sock, changes):
    send_string(sock, COMMAND_RUN)
    validate_response(sock, ACK)

    for change in changes:
        send_replacement(sock, change)

    send_string(sock, FIN)
    validate_response(sock, ACK)

    # wait for final FIN from server

    _, data = read_from_socket(sock)
    resp = data.decode()

    if resp == FIN:
       pass
    elif resp == ACK:
       pass
    else:
        logger.info(resp)
        raise ApsimProtocolError(f"Unexpected response during RUN: {resp}")
    print('run finished')

# ---------------------------
# READ OUTPUT
# ---------------------------
def read_output(sock, tablename, param_list):
    send_string(sock, COMMAND_READ)
    validate_response(sock, ACK)

    send_string(sock, tablename)
    validate_response(sock, ACK)

    for param in param_list:
        send_string(sock, param)
        validate_response(sock, ACK)

    send_string(sock, FIN)
    # validate_response(sock, FIN)

    results = {}
    send_string(sock, ACK)

    for param, dtype in param_list.items():
        results[param] = read_output_of_one(sock, dtype)
        send_string(sock, ACK)

    return results


def read_output_of_one(sock, param_type):
    size, data = read_from_socket(sock)

    if param_type == c_int32:
        fmt = f'{size // 4}i'
        return struct.unpack(fmt, data)

    elif param_type == c_double:
        fmt = f'{size // 8}d'
        return struct.unpack(fmt, data)

    elif param_type == c_char:
        return data.decode()

    else:
        raise ValueError("Unknown param type")


# ---------------------------
# START SERVER
# ---------------------------
def fix_datastore_location(model):
    from apsimNGpy import ApsimModel
    try:
        model = ApsimModel(model)

        model.add_new_model(
            parent_type="Models.Core.Simulations",
            parent_identifier="Simulations", replace=True,
            source={
                "$type": "Models.Storage.DataStore, Models",
                "Name": "DataStore",
                "Enabled": True,
                'ReadOnly': False
            }
        )
        return model.path
    except Exception as e:
        logger.error(e)


def start_apsim_server(server_path, file_path, host='0.0.0.0', port=27747, use_dll=False):
    server_path = Path(server_path)
    file_path = Path(file_path).resolve()

    system = platform.system()

    # 🔥 Resolve executable based on OS
    if system == "Windows":
        exe = server_path / "apsim-server.exe" if not use_dll else server_path / "apsim-server.dll"
    elif system in ("Linux", "Darwin"):  # Darwin = macOS
        exe = server_path / "apsim-server" if not use_dll else server_path / "apsim-server.dll"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

    if not exe.exists():
        raise FileNotFoundError(f"APSIM server not found: {exe}")

    # 🔥 Ensure executable permission on Unix
    if system in ("Linux", "Darwin"):
        exe.chmod(exe.stat().st_mode | 0o111)
    if not Path(exe).exists():
        print('exe', '===============================\n==================')
        raise FileNotFoundError(f"APSIM server not found")
    bdir = r'D:\package\ApsimX\bin\Debug\net8.0\apsim-server.exe'
    cmd = [
        str(exe),
        "--file", str(file_path),
        "--verbose",
        "--keep-alive",
        "--native",
        "--remote",
        "--address", host,
        "--port", str(port),

    ]
    if Path(exe).suffix == '.dll':
        cmd.insert(0, "dotnet")
    #  Use model directory as working dir (IMPORTANT)
    cwd = str(Path(bdir).parent)
    try:
        return subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,  # optional (for debugging)
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        logger.error(f"Unable to start APSIM server: {cmd}, exception: {e}")


# MAIN
# ---------------------------
if __name__ == '__main__':
    SERVER_PATH = configuration.bin_path
    JSON_PATH = str(Path(configuration.bin_path).parent / 'Examples')
    JSON_NAME = 'Wheat.apsimx'

    start_apsim_server(SERVER_PATH, JSON_PATH, JSON_NAME)

    sock = connect_to_remote_server("127.0.0.1", 27747)
    print("Connected")
    from numpy import arange

    for i in arange(1, 3, 0.5):
        print(i)
        changes = [{
            'path': '[Wheat].Leaf.Photosynthesis.RUE.FixedValue',
            'value': float(i),
            'paramtype': PROPERTY_TYPE_DOUBLE
        }]

        run_with_changes(sock, changes)

        results = read_output(sock, 'Report', {
            'Yield': c_double,
            'Clock.Today': c_double
        })

        print(pd.DataFrame(results))
