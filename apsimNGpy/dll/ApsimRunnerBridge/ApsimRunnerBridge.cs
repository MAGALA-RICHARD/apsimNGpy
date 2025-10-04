using System;
using System.IO;
using Models.Core;
using Models.Core.Run;
using APSIM.Shared.Utilities;

namespace ApsimRunnerBridge
{
    public static class Bridge
    {
        /// <summary>
        /// Run an APSIM Next Gen .apsimx file and return the database path.
        /// </summary>
        /// <param name="apsimxPath">Path to the .apsimx file.</param>
        /// <param name="apsimBinPath">Optional: APSIM binary folder containing Models.dll.</param>
        /// <param name="dbPath">Optional: Output database path (.db). Default: same as apsimxPath with .db suffix.</param>
        /// <param name="nProcessors">Number of processors to use. Default = system CPU count.</param>
        /// <param name="runPost">Run post-simulation tools. Default = false.</param>
        /// <param name="runTests">Run tests. Default = false.</param>
        /// <returns>Path to the generated .db file.</returns>
        public static string RunApsim(string apsimxPath,
                                      string apsimBinPath = null,
                                      string dbPath = null,
                                      int nProcessors = 0,
                                      bool runPost = false,
                                      bool runTests = false)
        {
            if (string.IsNullOrEmpty(apsimxPath) || !File.Exists(apsimxPath))
                throw new FileNotFoundException($"APSIMX file not found: {apsimxPath}");

            // Resolve APSIM_BIN_PATH
            if (string.IsNullOrEmpty(apsimBinPath))
                apsimBinPath = Environment.GetEnvironmentVariable("APSIM_BIN_PATH");

            if (string.IsNullOrEmpty(apsimBinPath) || !File.Exists(Path.Combine(apsimBinPath, "Models.dll")))
                throw new InvalidOperationException(
                    "APSIM_BIN_PATH is not set. Set it to the folder that contains Models.dll (e.g., C:\\Program Files\\APSIM2025.xx.xxxx.0).");

            // Load APSIM assemblies
            var modelsPath = Path.Combine(apsimBinPath, "Models.dll");
            var asm = System.Reflection.Assembly.LoadFrom(modelsPath);

            // Create datastore location
            dbPath ??= Path.ChangeExtension(apsimxPath, ".db");
            if (File.Exists(dbPath))
                File.Delete(dbPath);

            // Open and run
            var sims = FileFormat.ReadFromFile<Simulations>(apsimxPath);
            sims.FileName = apsimxPath;
            sims.DataStore.UseInMemoryDB = false;
            sims.DataStore.FileName = dbPath;

            if (nProcessors <= 0)
                nProcessors = Environment.ProcessorCount;

            var runner = new Runner(sims,
                                    runSimulations: true,
                                    runPostSimulationTools: runPost,
                                    runTests: runTests,
                                    wait: true,
                                    numberOfProcessors: nProcessors);

            runner.Run();
            runner.DisposeStorage();

            return dbPath;
        }
    }
}
