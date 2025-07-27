namespace CastBridge
{
    /// <summary>
    /// A static helper class to support type casting of APSIM base objects
    /// (e.g., Node, Model, IModel) to their actual derived types when using
    /// PythonNet. PythonNet often binds to the base class reference and
    /// does not automatically resolve the true runtime type. This utility
    /// allows for explicit casting from Python.
    /// casts only class objects
    /// </summary>
    public static class CastHelper
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
