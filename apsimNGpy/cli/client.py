# this an evolving module acording to github issue No#

import typer
import requests

app = typer.Typer()

BASE_URL = "http://127.0.0.1:8000"

@app.command()
def version():
    """Get APSIM version from the server."""
    response = requests.get(f"{BASE_URL}/version")
    if response.ok:
        typer.echo(f"APSIM Version: {response.json()['apsim_version']}")
    else:
        typer.echo("Failed to fetch version.")

@app.command()
def get_path():
    """Get current APSIM bin path."""
    response = requests.get(f"{BASE_URL}/get-path")
    if response.ok:
        typer.echo(f"Current APSIM bin path: {response.json()['current_bin_path']}")
    else:
        typer.echo("Failed to fetch bin path.")

@app.command()
def set_path(path: str):
    """Set the APSIM bin path."""
    response = requests.get(f"{BASE_URL}/set-path", params={"update": path})
    if response.ok:
        typer.echo(response.json()["message"])
    else:
        typer.echo(f"Error: {response.status_code} - {response.text}")

@app.command()
def auto_detect():
    """Auto detect APSIM bin path."""
    response = requests.get(f"{BASE_URL}/auto-detect")
    if response.ok:
        typer.echo(f"Detected: {response.json()['detected_path']}")
    else:
        typer.echo("No bin path detected.")
@app.command()
def load(name: str) -> str:
    """Send a request to load the model on the server."""
    response = requests.post(f"{BASE_URL}/load", json={"name": name})
    response.raise_for_status()
    print('loaded')
    return response.json()["message"]
@app.command()
def run() -> str:
    """Trigger model execution on the server."""
    response = requests.post(f"{BASE_URL}/run")
    response.raise_for_status()
    return response.json()["message"]
@app.command()
def inspect(_model:str):
    response = requests.get(f"{BASE_URL}/inspect", json={"_model": _model})
    if response.ok:
        typer.echo(f"Detected: {response.json()["model_inspect"]}")
    else:
        typer.echo("No model inspected.")

if __name__ == "__main__":
    app()
