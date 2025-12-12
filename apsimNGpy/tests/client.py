# apsim_client.py
import socket

HOST = "127.0.0.1"
PORT = 5055

def run_apsim(path: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.send(path.encode())
        data = s.recv(4096).decode()
    return data


if __name__ == "__main__":
    import os
    from pathlib import Path
    from apsimNGpy.core.config import load_crop_from_disk
    from apsimNGpy.core_utils.database_utils import get_db_table_names, read_db_table

    # Build maize example
    mp = os.path.realpath(load_crop_from_disk("Maize", "out.apsimx"))

    result = run_apsim(mp)

    print("APSIM finished. Version:", result)
    db = Path(mp).with_suffix(".db")
    if db.exists():
        print('exists')
    dbs = get_db_table_names(Path(mp).with_suffix(".db"))
    print(dbs)
