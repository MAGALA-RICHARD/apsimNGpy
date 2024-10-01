# Steps for installing apsimNGpy
apsimNGpy requires the following requirements  
\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*  
1\. Dotnet, install from https://learn.microsoft.com/en-us/dotnet/core/install/  
2\. Python3  
3\. APSIM Binary from https://apsim.info  
4\. Minimum; 8GM RAM  
5\. APSIM next generation installation  
APSIM can be downloaded on the apsim website here https://registration.apsim.info/  
form MaCOS and linus users follow the following installation in the link below  
https://apsimnextgeneration.netlify.app/install/  
if you are beginners, there are a couple of documentations here https://apsimnextgeneration.netlify.app/user_tutorials/

# Now you are ready to install apsimNGpy

Installation

* * *

Please note that all versions are currently in development, phase and they can be installed as follows:

- Step 1:  
    After downloading and installing APSIM Its important to keep track of the location of installation of APSIM binary files.  
    We shall shall use in step 3.  
    This location of this folder will depend on the operating System.

In windows it will be located in /  
there is an option to select the installation path on installation. Whatever, path you select, pelase copy the path before clicking next

In linux it usually is in /usr/local/lib/apsim/{APSIM VERSION}/bin e.g.  
/usr/local/lib/apsim/2024.8.7571.0/bin

We will need this value for later usage before running the APSIM File Successfully.

\-STEP 2:

\-- Either install from PyPI

.. code:: bash

```
pip install apsimNGpy
```

\-- Or clone the current development repository

.. code:: bash

```
git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git@dev
cd apsimNGpy
pip install .
```

You could also install using pip directly from github.

.. code:: bash

```
 pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git@development
```

l/lib/apsim/2024.8.7571.0/bin