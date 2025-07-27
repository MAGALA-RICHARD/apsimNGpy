CastBridge
===============

This is a static helper class designed to support type casting of APSIM base objects—such as Node, Model, and IModel—to their actual derived types when working with PythonNet. PythonNet often binds to base class references and does not automatically resolve the true runtime type. This utility provides explicit casting support from Python, and is intended for use with class objects only.

The associated DLL was compiled using .NET 6.0.3 as the target framework. However, because the code is generic and does not import or depend on any external libraries, we expect it to be compatible across other .NET framework versions without breaking.