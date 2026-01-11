.. what_is_new

What is New in **apsimNGpy 1.0.0**
===================================
**apsimNGpy 1.0.0** represents a major milestone in the development of the framework, transitioning from an experimental research tool to a stable, production-ready release. This version consolidates years of development and introduces several key improvements in performance, usability, reproducibility, and analytical capability.

``1. Stable, Reproducible Release``
---------------------------------------
* First **official 1.0.0** version, signifying a **stable API** and backward compatibility guarantee for future minor releases.

``2. Core Engine Improvements``
_________________________________
* **Refactored multiprocessing engine** for robust, scalable execution across multiple CPU cores, including safer handling of parallel APSIM runs on Windows.
* **Improved failure reporting** and retry mechanisms with configurable policies (e.g., `tenacity`-based retries), reducing silent errors in large batch jobs.
* **Improve job submissions** allowing edits to be submitted simultaneously.

``3. Expanded Sensitivity & Uncertainty Analysis``
___________________________________________________
* Updated **Sobol sampling** with configurable skip values for improved space-filling design.
* Clean handling of **calc_second_order** options with consistent propagation between sampling and analysis layers.
* Support for additional SALib methods with stable default parameterization.
* Sensitivity analysis workflows fully compatible across all os platforms.

``4. Improved Database & Output Management``
_______________________________________________
* **Schema-hash table naming** to avoid SQLite collisions in parallel executions.
* Stable persistence layer with:
  * deterministic table identifiers
  * execution and process metadata
  * large result handling with chunked writes.
* Cleaner error handling for results writes under heavy parallel loads.

``5. Workflow & Developer Quality-of-Life``
___________________________________________
* First modules test using .bat scripts
* Support for locking APSIM versions to a specific project.

``6. Fixes & Stability Enhancements``
__________________________________
* Resolution of common parallel SQLite locking issues under heavy batch throughput.
* Deterministic hashing for table identifiers even in multiprocessing contexts.
* Guidance and preflight validation for schema drift, unsupported data types, and mixed index/column structures.
* Better error reporting for model editing callbacks and APSIM parameter sets.

``Summary``
____________
**apsimNGpy 1.0.0** delivers:

* A stable, reproducible foundation for agri-environmental modeling workflows
* Scalability, reliability for large batch, single and multi-objective experiments
* Better integration of APSIM with decision support, sensitivity, and spatial optimization routines
* An enduring API that is resilient and robust under a wide range of uncertainties

This release establishes a platform for future enhancements while remaining reliable for academic and applied research in productivity, environmental impacts, and landscape planning.

