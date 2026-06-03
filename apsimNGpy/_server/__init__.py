from ctypes import c_int32, c_double, c_char
import struct
import socket
import subprocess
import pandas as pd
from time import sleep
from pathlib import Path

ACK = 'ACK'
FIN = 'FIN'
COMMAND_RUN = 'RUN'
COMMAND_READ = 'READ'

PROPERTY_TYPE_INT = 0
PROPERTY_TYPE_DOUBLE = 1
PROPERTY_TYPE_STRING = 4
from apsimNGpy import configuration


def get_server(bin_path=configuration.bin_path):
    p = Path(bin_path).rglob('apsim-server.exe')
    return list(p)[0]


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


def read_from_socket(sock):
    header = recv_all(sock, 4)
    size = struct.unpack('<i', header)[0]
    data = recv_all(sock, size)
    return size, data


def validate_response(sock, expected):
    _, data = read_from_socket(sock)
    resp = data.decode()
    print(resp)
    if resp != expected:
        raise ValueError(f"Expected '{expected}', got '{resp}'")


# ---------------------------
# SEND HELPERS
# ---------------------------
def send_string(sock, value):
    send_to_socket(sock, value)


def send_int(sock, value):
    sock.send(struct.pack('<i', value))


def send_double(sock, value):
    sock.send(struct.pack('<d', value))


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
   # validate_response(sock, FIN)

    print("Run finished")


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
    validate_response(sock, FIN)

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
def start_apsim_server(server_path, json_path, json_name,
                       host='0.0.0.0', port=27747):
    file_path = f'{json_path}/{json_name}'
    cmd = [
        f'{server_path}/apsim-server.exe',
        "listen",
        "--file", file_path,
        "--native",
        "--remote",
        "--keep-alive",
        "--port", str(port),
        "--address", "127.0.0.1",
        "--verbose"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return proc


# ---------------------------
# MAIN
# ---------------------------
if __name__ == '__main__':
    SERVER_PATH = configuration.bin_path
    JSON_PATH = str(Path(configuration.bin_path).parent / 'Examples')
    JSON_NAME = 'Wheat.apsimx'

    #start_apsim_server(SERVER_PATH, JSON_PATH, JSON_NAME)
    sleep(2)
    sock = connect_to_remote_server("127.0.0.1", 27746)
    print("Connected")
    from numpy import arange

    for i in arange(1, 3, 0.5):
        print(i)
        changes = [{
            'path': '[Leaf].Photosynthesis.RUE.FixedValue',
            'value': float(i),
            'paramtype': PROPERTY_TYPE_DOUBLE
        }]

        run_with_changes(sock, changes=[])

        results = read_output(sock, 'Report', {
            'Yield': c_double,
            'Clock.Today': c_double
        })

        print(pd.DataFrame(results))
