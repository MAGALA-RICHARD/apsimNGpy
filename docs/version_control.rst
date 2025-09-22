Version Control and APSIM Compatibility in apsimNGpy
=====================================================

The ``apsimNGpy`` package is designed to interface with any version of the APSIM Next Generation (APSIM NG) platform. However, because APSIM NG is under continuous development, changes in its internal structure, APIs, or file formats may occasionally lead to version-breaking issues that affect ``apsimNGpy`` functionality.

.. tip::

    To manage this, an automated robot runs **every two days** to check for new APSIM NG development releases. It performs the following tasks:

    1. **Downloads and installs** the latest APSIM NG development version.
    2. **Runs the complete ``apsimNGpy`` unit test suite** against the new APSIM version.
    3. **Sends a detailed report** of the test outcomes to the ``apsimNGpy`` administrators.
    4. If all tests **pass successfully**, the new APSIM version is marked as the ``latestunit apsimNGpy::version`` and is published on the documentation homepage.

    A button on the homepage links directly to the download page for the tested APSIM version. Please register to access the download.

    This workflow ensures that users always have access to a known-compatible APSIM version when using ``apsimNGpy``.


.. admonition:: In Case of Errors

    If the automated test suite identifies **breaking changes** or **errors**, these are reviewed and addressed manually by the maintainers. The resolution time may vary depending on administrator availability.

    During this period:

    * **Bug fixes and patches** may be rolled out.
    * Compatibility notes or temporary workarounds may be posted on the repository or documentation site.

.. admonition:: Best Practices for Users

    To ensure smooth and reliable use of ``apsimNGpy``, users are strongly encouraged to:

    * **Check the documentation homepage** to confirm the current ``latestunit apsimNGpy::version``.
    * **Stay updated** with the most recent version of ``apsimNGpy`` to benefit from improvements and compatibility updates.
    * If issues arise with a new APSIM version, **fall back to a previously tested version** known to work with your current ``apsimNGpy`` setup.


.. tip::

   APSIM has undergone three major version changes that introduced breaking changes for ``apsimNGpy``. This implies that there is high chance even for new versions not yet tested ``tested`` to still work.  Based on experience, about 98% do—thanks to apsimNGpy’s versatile API. However, if you hit a compatibility issue, please report it with your APSIM build number and a minimal example.

   In addition, while breaking changes can be inconvenient—and have led some APSIM wrappers to pin to fixed versions, apsimNGpy is built with forward  and backward-compatibility in mind and is actively synchronized with upstream APSIM.
   This philosophy lets researchers adopt APSIM improvements without reworking their pipelines, preserving reproducibility while enabling rapid iteration. This allows studies to be reproduced and extended as APSIM evolves.


