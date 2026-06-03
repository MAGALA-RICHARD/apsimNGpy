
from pathlib import Path

apsimNGpy — Module Overview
===============================

This document gives a **high-level map** of the repository so new contributors know
*where things live* and **what to expect** in each module. It is not an exhaustive
API reference—see inline docstrings and package docs for details.

Quick orientation
=================
- **Purpose**: Pythonic interface for **APSIM Next Generation (APSIM NG)**.
- **Style**: Primarily Object-oriented
- **Outputs**: Analysis-ready pandas DataFrames and lightweight artifacts for downstream ML/visualization.

Repository layout (top-level)
=============================

cli/
----
Command-line entry points and helpers for running common workflows without writing code.
Expect simple commands for: loading/running models, inspecting results, launching factorial
experiments, and kicking off optimization or parallel jobs.

*Expect to find*
  - Typer/Click style app, argument parsing, rich/ANSI output utilities.
  - Subcommands like ``run``, ``experiment``, ``optimize``, ``parallel`` (naming may vary).
  - Thin wrappers that call into `core`, `manager`, `optimizer`, `parallel`.

./core/
-----
The **heart of the package**—Python wrappers over APSIM NG models and files.
This is the end point for Python communication with the Csharp assemblies for APSIM model.


./core_utils/
-----------
Low-level utilities that support :mod:`core`: type conversion, path/address helpers for APSIM
component trees, validation of fields/units, serialization glue. contains database utils, timers, and progressbars


dll/
----
Binaries or loaders related to the APSIM/.NET runtime. Usually **not modified**
by end users. the dll in this directory is compiled to facilitate type conversion of APSIM classes to their respective reference types


examples/
---------
Minimal, **copy-pasteable** scripts and notebooks demonstrating typical tasks.


images/ & logo/
---------------
Static assets for docs, README badges, and diagrams. **No code** here.

manager/
--------
contains low level API for downloading soil and weather

optimizer/
----------
Optimization tooling for calibration and policy search, such as trade-off analysis.

*Expect to find*
  - Problem definitions (e.g., **MixedVariable**, **MultiObjectiveProblem**).
  - Hooks to external solvers (SciPy/pymoo, etc.) and evaluation loops that call **ApsimModel**.
  - Patterns for single- and multi-objective runs (yield–profit–N loss–SOC, etc.).

parallel/
---------
Parallel and asynchronous execution utilities.

*Expect to find*
  - Multi-process / multi-thread runners, job queues, live progress/ETA.
  - Memory-aware result retrieval (on-demand) and run collation.
  - used by APIs like **MultiCoreManager** to distribute simulations across cores.

raw_docs/
---------
Source material for documentation (drafts, RST/MD fragments, figures). these are shipped to another repo gor hosting

scratch/
--------
A temporary **workbench** for local experiments, quick scripts, or generated artifacts that
should not be treated as API. Contents are typically non-critical.

tests/
------
Automated tests (unit/integration). Start here to see **canonical usage**.

*Expect to find*
  - Fixtures that create/load small ``.apsimx`` demos.
  - Assertions on outputs (columns, units), performance, and error handling.


validation/
-----------
Lightweight model evaluation metrics for model prediction.

visual/
-------
utilities in this directory are deprecated.
Plotting and reporting helpers. Thin wrappers around **matplotlib**/**pandas** (and optionally
seaborn) to standardize figures for papers or dashboards.

w/
--
Internal workspace or **experimental** area (name suggests “workbench”). Treat as
non-API; stabilize/relocate items when they mature.

__pycache__/ & .idea/ & .DS_Store
---------------------------------
Editor and runtime artifacts—safe to ignore. Not part of the package API.

Top-level Python modules
========================

__init__.py
-----------
Defines the public package surface (what gets imported on ``from apsimNGpy import *``). Often
re-exports key classes like **ApsimModel**, managers, and version metadata.

version.py
----------
Single source of truth for the package version (used by packaging/CI and ``__version__``).

settings.py
-----------
Default application settings and environment integration. Typical use cases include locating
APSIM NG binaries, toggling parallel backends, and setting I/O defaults.


exceptions.py
-------------
Custom exception types that make error handling explicit (e.g., missing APSIM runtime,
invalid model path, or illegal edit operations).


CITATION.cff
------------
Citation metadata so others know **how to cite** the package in papers.

Conventions & contribution notes
================================

- **Public API lives in** `core`, `manager`, `optimizer`, `parallel`, :mod:`visual`.
- **General Internal helpers** live under `core_utils`
- Keep notebooks and long-form examples in `examples` and docs in `raw_docs`.
- Tests are first-class citizens—mirror examples with assertions in `tests`.
