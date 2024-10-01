# Changing the APSIM binary installation path
APSIMNGpy requires a reference path to your installation directory to communicate with .NET. If you're fortunate, this path is automatically added to the Windows system environment variables during installation. However, if it's not, there are two ways to manually configure it.

* 1. Approach use the apsimNGpy config module
   
```
from apsimnnGpy.config import set_apsim_bin_path
# takes in one argument the path to the binaries; they should end with the word bin
apsm_bin_path = 'path/toyour bin'/bi
change_apsim_bin_path(apsm_bin_path)
```

If the path is incorrect, APSIMNGpy will fail to function and will throw an error when attempting to start Pythonnet. Additionally, please be aware that this process of changing the path was originally managed by the `Config` class, but this class has since been deprecated.
* 2.  Edit the system's environmental variable
   please follow the link below, but at the last steps,  The variable name should be APSIM
   and the variable value is the path to the binary installation path. for Windows users only
   https://www.imatest.com/docs/editing-system-environment-variables/#Windows
  