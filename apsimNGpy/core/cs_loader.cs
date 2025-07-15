using System;
using System.IO;
using Models.Core;

namespace ApsimInterop
{
    public static class ApsimLoader
    {
        /// <summary>
        /// Loads a Simulations object from either a JSON string, a file path, or a model object.
        /// </summary>
        /// <param name="input">Either a .apsimx file path or a JSON string</param>
        /// <param name="isJsonString">Set to true if input is a JSON string, false if it's a file path</param>
        /// <returns>A Simulations object</returns>
        public static Simulations LoadSimulations(string input, bool isJsonString)
        {
            if (string.IsNullOrWhiteSpace(input))
                throw new ArgumentException("Input cannot be null or empty.");

            FileFormat fileFormat = new FileFormat();
            if (isJsonString)
            {
                // Load from JSON string
                var result = fileFormat.ReadFromString<Simulations>(input, null, true);
                return result?.Model as Simulations;
            }
            else
            {
                // Load from .apsimx file path
                if (!File.Exists(input))
                    throw new FileNotFoundException($"File not found: {input}");

                var result = fileFormat.ReadFromFile<Simulations>(input, true);
                return result?.Model as Simulations;
            }
        }
    }
}
