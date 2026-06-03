# apsim.py
import argparse
import requests

SERVER = "http://127.0.0.1:8000"

def load_model(name):
    r = requests.post(f"{SERVER}/load", json={"name": name})
    print(r.json()["message"])

def run_model():
    r = requests.post(f"{SERVER}/run")
    print(r.json()["message"])

def inspect_model():
    r = requests.get(f"{SERVER}/inspect")
    print("Model State:")
    for k, v in r.json().items():
        print(f"  {k}: {v}")
def inspect():
    r = requests.post(f"{SERVER}/inspect")
    print(r.json()["message"])


def main():
    parser = argparse.ArgumentParser(prog="apsim", description="APSIM CLI")
    subparsers = parser.add_subparsers(dest="command")

    load = subparsers.add_parser("load")

    load.add_argument("name")

    subparsers.add_parser("run")
    subparsers.add_parser("inspect")

    args = parser.parse_args()

    if args.command == "load":
        load_model(args.name)
    elif args.command == "run":
        run_model()
    elif args.command == "inspect":
        inspect_model()
    elif args.command == "ins":
        inspect()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
