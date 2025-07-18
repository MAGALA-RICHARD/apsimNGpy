import subprocess
import os
from pathlib import Path
import shutil

# Settings
project_name = "CastBridge"
cs_filename = "CastHelpers.cs"
dll_output_path = Path("build_output")  # where the final DLL will be copied
cs_code = """
    namespace CastBridge
{
    /// <summary>
    /// A static helper class to support type casting of APSIM base objects
    /// (e.g., Node, Model, IModel) to their actual derived types when using
    /// PythonNet. PythonNet often binds to the base class reference and
    /// does not automatically resolve the true runtime type. This utility
    /// allows for explicit casting from Python.
    /// </summary>
    public static class CastHelpers
    {
        /// <summary>
        /// Generic method to safely cast an object to a specified reference type.
        /// Returns null if the cast is not valid.
        /// </summary>
        /// <type param name="T">The target type to cast to (e.g., Simulation, Zone, Manager).</typeparam>
        /// <param name="obj">The object to cast. Normally the Model attached to node</param>
        /// <returns>The object as type T, or null if the cast fails.</returns>
        public static T CastAs<T>(object obj) where T : class
        {
            return obj as T;
        }
    }
}

"""

# Create project directory
project_dir = Path.cwd() / project_name
if project_dir.exists():
    shutil.rmtree(project_dir)
subprocess.run(["dotnet", "new", "classlib", "-n", project_name], check=True)

# Overwrite Class1.cs with your CastHelpers.cs
src_file = project_dir / "CastHelpers.cs"
with open(src_file, "w") as f:
    f.write(cs_code)

# Remove the default Class1.cs
default_class = project_dir / "Class1.cs"
if default_class.exists():
    default_class.unlink()

# Build the project
subprocess.run(["dotnet", "build", "-c", "Release"], cwd=project_dir, check=True)

# Locate and copy the DLL
release_dir = project_dir / "bin" / "Release"
dll_files = list(release_dir.rglob(f"{project_name}.dll"))
if dll_files:
    dll_output_path.mkdir(exist_ok=True)
    final_path = dll_output_path / dll_files[0].name
    shutil.copy(dll_files[0], final_path)
    print(f"✅ Compiled DLL saved to: {final_path}")
else:
    print("❌ Build failed or DLL not found.")
