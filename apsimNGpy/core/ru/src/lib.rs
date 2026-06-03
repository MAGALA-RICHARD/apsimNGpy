use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

use std::process::{Command, Stdio};
use std::time::Duration;
use wait_timeout::ChildExt;

#[pyclass]
struct ApsimResult {
    #[pyo3(get)]
    stdout: String,

    #[pyo3(get)]
    stderr: String,

    #[pyo3(get)]
    returncode: i32,
}

#[pyfunction]
#[pyo3(
    signature = (
        models,
        apsim_exec,
        timeout=800,
        n_cores=-1,
        verbose=false,
        to_csv=false
    )
)]
fn run_apsim_by_path(
    models: Vec<String>,
    apsim_exec: String,
    timeout: u64,
    n_cores: i32,
    verbose: bool,
    to_csv: bool,
) -> PyResult<ApsimResult> {

    let mut cmd = Command::new(&apsim_exec);

    for model in models.iter() {
        cmd.arg(model);
    }

    cmd.arg("--cpu-count").arg(n_cores.to_string());

    if verbose {
        cmd.arg("--verbose");
    }

    if to_csv {
        cmd.arg("--csv");
    }

    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child = cmd.spawn()
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to start APSIM: {}", e)))?;

    let timeout_duration = Duration::from_secs(timeout);

    let status = child.wait_timeout(timeout_duration)
        .map_err(|e| PyRuntimeError::new_err(format!("Timeout error: {}", e)))?;

    if status.is_none() {
        child.kill().ok();
        return Err(PyRuntimeError::new_err(
            format!("APSIM execution exceeded timeout ({} seconds)", timeout)
        ));
    }

    let output = child.wait_with_output()
        .map_err(|e| PyRuntimeError::new_err(format!("Failed to read APSIM output: {}", e)))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    let code = output.status.code().unwrap_or(-1);

    if code != 0 {
        return Err(PyRuntimeError::new_err(
            format!(
                "APSIM failed (exit code {})\nSTDERR:\n{}\nSTDOUT:\n{}",
                code, stderr, stdout
            )
        ));
    }

    Ok(ApsimResult {
        stdout,
        stderr,
        returncode: code,
    })
}

#[pymodule]
fn apsim_runner(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run_apsim_by_path, m)?)?;
    m.add_class::<ApsimResult>()?;
    Ok(())
}