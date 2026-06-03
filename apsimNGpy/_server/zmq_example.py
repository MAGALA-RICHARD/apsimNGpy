import zmq
import msgpack
import subprocess
import psutil
import time
import pandas as pd
from pathlib import Path

# Set up a listening server on a random port
import zmq
import subprocess
from pathlib import Path


def test_proto2(apsim_dir):
    apsim = {}

    context = zmq.Context()

    # ✅ Use REP for interactive mode
    socket = context.socket(zmq.REP)

    # Bind to a random available port
    socket.bind("tcp://127.0.0.1:0")

    endpoint = socket.getsockopt(zmq.LAST_ENDPOINT).decode()
    port = endpoint.split(":")[-1]

    apsim['apsim_socket'] = socket
    apsim['random_port'] = port

    print("Listening on", endpoint)

    # Path to APSIM ZMQ server
    EXE = Path(apsim_dir) / 'ApsimZMQServer.dll'
    assert EXE.exists(), f"Binary not found: {EXE}"

    # ✅ Start APSIM process
    apsim['process'] = subprocess.Popen([
        'dotnet',
        str(EXE),
        "-p", port,
        "-P", "interactive",
        "-f", "ZMQ-sync.apsimx"
    ])

    print("Started APSIM process id", apsim['process'].pid)

    return apsim


# Send a command, eg resume/set/get
def send_command(socket, command, args=None):
    socket.send_string(command, zmq.SNDMORE if args else 0)
    if args:
        for i, arg in enumerate(args):
            socket.send(msgpack.packb(arg), zmq.SNDMORE if i < len(args) - 1 else 0)


# The response loop. When the simulation connects we tell it what to do.
# connect -> ok
# paused -> resume/get/set
# finished -> ok

def poll_zmq2(socket):
    print("Waiting for zmq messages")
    while True:
        print("t")
        msg = socket.recv_string()
        print(msg, 'msg', flush=True)
        if msg == "connect":
            send_command(socket, b"ok")
        elif msg == "paused":
            send_command(socket, "get", ["[Clock].Today.Day"])
            reply = msgpack.unpackb(socket.recv())
            assert isinstance(reply, int)

            send_command(socket, "get", ["[Wheat].Phenology.Zadok.Stage"])
            reply = msgpack.unpackb(socket.recv())
            assert isinstance(reply, float)

            send_command(socket, "get", ["[Soil].Water.PAW"])
            reply = msgpack.unpackb(socket.recv())
            assert isinstance(reply, list) and len(reply) == 7

            send_command(socket, "get", ["[Nutrient].NO3.kgha"])
            reply = msgpack.unpackb(socket.recv())
            # print(reply)

            send_command(socket, "set", ["[Nutrient].NO3.kgha", [2 * ele for ele in reply]])
            msg = socket.recv_string()

            send_command(socket, "get", ["[Nutrient].NO3.kgha"])
            reply = msgpack.unpackb(socket.recv())
            print(reply)

            send_command(socket, "get", ["[Manager].Script.DummyStringVar"])
            reply1 = msgpack.unpackb(socket.recv())

            send_command(socket, "set", ["[Manager].Script.DummyStringVar", "Blork"])
            msg = socket.recv_string()

            send_command(socket, "get", ["[Manager].Script.DummyStringVar"])
            reply2 = msgpack.unpackb(socket.recv())
            assert reply1 != reply2

            send_command(socket, "set", ["[Manager].Script.DummyStringVar", reply1])
            msg = socket.recv_string()

            send_command(socket, "set", ["[Manager].Script.DummyDoubleVar", 42.42])
            msg = socket.recv_string()

            send_command(socket, "resume")
        elif msg == "finished":
            send_command(socket, b"ok")
            break


def close_zmq2(apsim):
    apsim['apsim_socket'].close()
    apsim['process'].terminate()
    process = psutil.Process(apsim['process'].pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


# apsim_dir = "/home/trs07170/Research/Pan/ApsimX"

apsim_dir = r'C:\\Users\\rmagala\\AppData\\Local\\Programs\\APSIM2026.4.8027.0\\bin'
apsim = test_proto2(apsim_dir)
rec = {"iter": [], "mem": [], "time": []}

for i in range(10):
    print(i)
    start_time = time.time()
    poll_zmq2(apsim['apsim_socket'])
    proc = psutil.Process(apsim['process'].pid)
    mem_info = proc.memory_info().rss
    elapsed_time = time.time() - start_time
    rec["iter"].append(i + 1)
    rec["mem"].append(mem_info)
    rec["time"].append(elapsed_time)

close_zmq2(apsim)
print(pd.DataFrame(rec))
