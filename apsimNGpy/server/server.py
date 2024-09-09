"""
ttt
"""

import struct
import socket
import pandas as pd
from time import sleep
from ctypes import c_int32, c_double, c_char
from .. import settings

import os
from pathlib import Path
from apsimNGpy.config import load_python_net
from apsimNGpy.data.base_data import LoadExampleFiles
import clr  # this should be import after importing pythonnet_config
from System.Collections.Generic import *

pat = settings.APSIM_PATH
server_path = os.path.join(pat, 'apsim-server.dll')
clr.AddReference(server_path)

import APSIM

maize = LoadExampleFiles(Path.home())
APSIM.Server.ApsimServer  # statrt again from here
# decorator to monitor performance
serv = APSIM.Server.Cli.GlobalServerOptions()
serv.KeepAlive = False
serv.Verbose = True
serv.File = maize.get_maize
serv.Verbose = True
serv.NativeMode = True
serv.LocalMode = True
serv.SocketName = 'maga'
ac = APSIM.Server.ApsimServer(serv)
from ctypes import c_int32, sizeof, c_double, c_char, c_int64

class ApsimClient:
    ACK = 'ACK'
    FIN = 'FIN'
    COMMAND_RUN = 'RUN'
    COMMAND_READ = 'READ'
    commandVersion = 'VERSION'
    PROPERTY_TYPE_INT = 0
    PROPERTY_TYPE_DOUBLE = 1
    PROPERTY_TYPE_BOOL = 2
    PROPERTY_TYPE_DATE = 3
    PROPERTY_TYPE_STRING = 4
    PROPERTY_TYPE_INT_ARRAY = 5
    PROPERTY_TYPE_DOUBLE_ARRAY = 6
    PROPERTY_TYPE_BOOL_ARRAY = 7
    PROPERTY_TYPE_DATE_ARRAY = 8
    PROPERTY_TYPE_STRING_ARRAY = 9
    PATH = server_path
    APSIM_PATH = maize

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port


    def connect_to_remote_server(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((self.ip_address, self.port))
            return client
        except ConnectionRefusedError as e:
           print("connection denied-----------/")


    def _disconnect_from_server(self, socket):
        socket.close()

    def send_to_socket(self, socket, msg, slen):
        if isinstance(msg, int):
            msg = struct.pack('<i', msg)
        elif isinstance(msg, float):
            msg = struct.pack('<d', msg)
        elif isinstance(msg, str):
            msg = struct.pack('<' + str(slen) + 's', msg.encode())
        slen = struct.pack('<i', slen)
        socket.send(slen)
        socket.send(msg)

    def send_string_to_socket(self, socket, msg):
        # length = len(msg.encode())
        # slen = '%08d' % lengthy
        # socket.sendall(msg.encode())
        # print(msg)
        self.send_to_socket(socket, msg, len(msg))

    def read_from_socket(self, socket):
        header = socket.recv(4)
        # print(header)
        recv_size = struct.unpack('<i', header)[0]
        recv_data = socket.recv(recv_size)

        # recv_size = 0
        # recv_data = b''
        # while recv_size < total_size:
        #     data = socket.recv(1024)
        #     recv_size += len(data)
        #     recv_data += data
        return recv_size, recv_data

    def validate_response(self, socket, expected):
        data_size, data = self.read_from_socket(socket)

        resp = data.decode("utf-8")

        assert resp == expected, "Expected response '%s' but got '%s'\n" % (expected, resp)

    def send_int(self, socket, paramType):
        msg = struct.pack('<i', paramType)
        socket.send(msg)

    def send_double(self, socket, paramValue):
        msg = struct.pack('<d', paramValue)
        socket.send(msg)

    def send_string(self, socket, paramValue):
        msg = struct.pack('<' + str(len(paramValue)) + 's', paramValue.encode())
        socket.send(msg)

    def send_replacement_to_socket(self, socket, change):
        # 1. Send parameter path.
        self.send_string_to_socket(socket, change["path"])
        self.validate_response(socket,self.ACK)

        # 2. Send parameter type.
        self.send_int(socket, change["paramtype"])
        # send_to_socket(socket, change["paramtype"],sizeof(c_int32) )#
        self.validate_response(socket, self.ACK)

        # 3. Send the parameter itself.
        if isinstance(change["value"], float):
            # print(change["value"])
            # typeofvalue = c_double
            self.send_double(socket, change["value"])
            # send_to_socket(socket, change["value"], sizeof(typeofvalue))
        elif isinstance(change["value"], int):
            # typeofvalue = c_int32
            self.send_int(socket, change["value"])
            # send_to_socket(socket, change["value"], sizeof(typeofvalue))
        elif isinstance(change["value"], str):
            self.send_string(socket, change["value"])
            # send_string_to_socket(socket, change["value"])
        self.validate_response(socket, self.ACK)

    def run_with_changes(self, socket, changes):
        self.send_string_to_socket(socket, self.COMMAND_RUN)
        self.validate_response(socket, self.ACK)
        for i in range(len(changes)):
            self.send_replacement_to_socket(socket, changes[i])

        self.send_string_to_socket(socket, self.FIN)
        self.validate_response(socket, self.ACK)
        self.validate_response(socket, self.FIN)
        print('Run Finished')

    def read_output(self, socket, tablename, param_list):
    # 1. Send READ command.
        self.send_string_to_socket(socket, self.COMMAND_READ)
        # 2. Receive ACK-> validate server received read commond
        self.validate_response(socket, self.ACK)
        # 3. Send table name.
        self.send_string_to_socket(socket, tablename)
        # 4. Receive ACK-> validate server received table name
        self.validate_response(socket, self.ACK)
        # 5. Send parameter names one at a time.
        for param_name in param_list:
            self.send_string_to_socket(socket, param_name)
            # Should receive ACK after each message.
            self.validate_response(socket, self.ACK)
        # Send FIN to indicate end of parameter names.
        self.send_string_to_socket(socket, self.FIN)
        # send_string_to_socket(socket, ACK)
        self.validate_response(socket, self.FIN)

        results = {}
        self.send_string_to_socket(socket, self.ACK)
        for param_name, param_type in param_list.items():
            # print(param_name,param_type)
            # send_string_to_socket(socket, ACK)
            result_output_of_one = self.read_output_of_one(socket, param_type)
            results[param_name] = result_output_of_one
            self.send_string_to_socket(socket, self.ACK)

        # validate_response(socket, ACK)#这里注意
        # validate_response(socket, ACK)
        # disconnect_from_server(socket)
        return results

    def read_output_of_one(self, socket, param_type):
        recv_size, recv_data = self.read_from_socket(socket)
        # print(recv_data)
        # print(recv_size)
        # fmt = (header//4)*'i'
        # recv_size = struct.unpack(fmt,header)
        # print(param_type)
        if param_type == c_int32:
            # result_of_one = result_of_one.decode()
            fmt = (recv_size // 4) * "i"
            result_of_one = struct.unpack(fmt, recv_data)  # [0]
        elif param_type == c_double:
            fmt = (recv_size // 8) * "d"
            # print(recv_data)
            result_of_one = struct.unpack(fmt, recv_data)  # [0]
        elif param_type == c_char:
            # result_of_one = struct.unpack('@s', recv_data)[0]
            result_of_one = recv_data.decode("utf-8")
        return result_of_one
        # clientSoscket.close()

    def start_apsim_server(self,  HOST='0.0.0.0', PORT=27747, SOCKETNAME='ApsimNGx'):
        import os
        import subprocess
        SERVER_PATH =pat
        sp = server_path.replace("dll", 'exe')
        fn = maize.get_maize
        dotnet =r'C:\Program Files\dotnet\sdk'
        random_port = "12345"
        command =[
            fn,
            "-p", random_port,
            '-f',fn,
            '-v',
            'k',
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        print(stdout.decode())
        print(stderr.decode())
        return stderr, stdout

if __name__ == '__main__':
    # Example usage:
    # JUST curious is there already a client someone can use. This seems to me to be an overkill.
    apsim_client = ApsimClient("10.24.22.192", 11)
    # You can now use apsim_client to interact with the Apsim server.
    lp= apsim_client.start_apsim_server()
    sock = apsim_client.connect_to_remote_server()
