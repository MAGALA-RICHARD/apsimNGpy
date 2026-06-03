import subprocess
import time
from pathlib import Path

import msgpack
import pandas as pd
import psutil
import zmq


# -----------------------------
# Start APSIM ZMQ server
# -----------------------------
def test_proto2(apsim_dir, apsim_file="ZMQ-sync.apsimx"):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    # Avoid hanging forever
    socket.setsockopt(zmq.RCVTIMEO, 10000)
    # socket.setsockopt(zmq.SNDTIMEO, 10000)

    # socket.bind("tcp://127.0.0.1:0")
    # socket = context.socket(zmq.REQ)
    port = '5555'
    socket.connect(f"tcp://127.0.0.1:{port}")

    endpoint = socket.getsockopt(zmq.LAST_ENDPOINT).decode()
    port = endpoint.rsplit(":", 1)[-1]

    exe = Path(apsim_dir) / "ApsimZMQServer.exe"
    if not exe.exists():
        raise FileNotFoundError(f"Binary not found: {exe}")

    process = subprocess.Popen(
        [

            str(exe),
            "-p", port,
            '-P', "interactive",
            "-f", apsim_file,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print(f"Listening on {endpoint}")
    print(f"Started APSIM process id {process.pid}")
    time.sleep(2)

    return {
        "context": context,
        "socket": socket,
        "process": process,
        "port": port,
    }


# -----------------------------
# Send command
# -----------------------------
def send_command(socket, command, args=None):
    socket.send_string(command, zmq.SNDMORE if args else 0)

    if args:
        for i, arg in enumerate(args):
            more = zmq.SNDMORE if i < len(args) - 1 else 0
            socket.send(msgpack.packb(arg, use_bin_type=True), more)


# -----------------------------
# Receive helper
# -----------------------------
def recv_any(socket):
    raw = socket.recv()

    try:
        return raw.decode()
    except:
        return msgpack.unpackb(raw, raw=False)


# -----------------------------
# Main ZMQ loop
# -----------------------------
def poll_zmq2(socket):
    print("Talking to APSIM...")

    # Step 1: handshake
    socket.send_string("connect")
    msg = socket.recv_string()
    print("MSG:", msg)

    while True:
        # Step 2: ask APSIM for state
        socket.send_string("step")
        msg = socket.recv_string()
        print("MSG:", msg)

        if msg == "paused":
            # ---- GET ----
            send_command(socket, "get", ["[Clock].Today.Day"])
            _ = socket.recv()

            send_command(socket, "get", ["[Wheat].Phenology.Zadok.Stage"])
            _ = socket.recv()

            send_command(socket, "get", ["[Soil].Water.PAW"])
            _ = socket.recv()

            send_command(socket, "get", ["[Nutrient].NO3.kgha"])
            no3 = msgpack.unpackb(socket.recv())

            # ---- SET ----
            updated = [2 * x for x in no3]
            send_command(socket, "set", ["[Nutrient].NO3.kgha", updated])
            _ = socket.recv()

            # resume
            socket.send_string("resume")
            msg = socket.recv_string()

        elif msg == "finished":
            socket.send_string("ok")
            _ = socket.recv()
            break


# -----------------------------
# Cleanup
# -----------------------------
def close_zmq2(apsim):
    try:
        apsim["socket"].close(0)
    except:
        pass

    try:
        proc = apsim["process"]

        if proc.poll() is None:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                try:
                    child.kill()
                except:
                    pass
            parent.kill()
    except:
        pass

    try:
        apsim["context"].term()
    except:
        pass


# -----------------------------
# Run multiple iterations
# -----------------------------
if __name__ == "__main__":
    apsim_dir = r"C:\Users\rmagala\AppData\Local\Programs\APSIM2026.4.8027.0\bin"

    rec = {"iter": [], "mem": [], "time": []}

    for i in range(10):
        print(f"\n--- Iteration {i + 1} ---")

        apsim = test_proto2(apsim_dir)
        proc = apsim['process']

        start = time.time()

        try:
            poll_zmq2(apsim["socket"])
        except Exception as e:
            print("Error:", e)
            close_zmq2(apsim)
            continue

        elapsed = time.time() - start

        proc = psutil.Process(apsim["process"].pid)
        mem = proc.memory_info().rss

        rec["iter"].append(i + 1)
        rec["mem"].append(mem)
        rec["time"].append(elapsed)

        close_zmq2(apsim)

    print("\nResults:")
    print(pd.DataFrame(rec))
