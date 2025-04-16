import os
import sys
from version import __version__, __app_name__, __description__, __author__

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))

# Required TCL/TK files only
TCL_REQUIRED = [
    "tcl86t.dll",
    "tk86t.dll",
    "init.tcl",
    "tk.tcl",
    "ttk/*Theme.tcl",
    "ttk/ttk.tcl",
    "ttk/utils.tcl",
    "msgs/en*.msg"
]

# Explicit excludes for TCL/TK
TCL_EXCLUDES = [
    "demos/*",
    "tzdata/*",
    "opt/*",
    "tests/*",
    "encoding/*"
]

PACKAGES = [
    "tkinter",
    "tkcalendar",
    "babel.numbers",
    "matplotlib.backends.backend_tkagg"
]

INCLUDES = [
    "tkinter.ttk",
    "babel.numbers"
]

EXCLUDES = [
    "unittest", "email", "html", "http", "xml", "pydoc",
    "tornado", "traitlets", "win32api", "win32com",
    "matplotlib.tests", "numpy.random._examples",
    "zoneinfo", "pytz.zoneinfo", "babel.locale-data",
    "tkinter.test", "lib2to3", "distutils", "setuptools",
    "pip", "pkg_resources", "pytz"
]

BUILD_OPTIONS = {
    "packages": PACKAGES,
    "includes": INCLUDES,
    "excludes": EXCLUDES,
    "include_files": [
        (os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'), 'lib/tk86t.dll'),
        (os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'), 'lib/tcl86t.dll'),
        ('medical_office.db', 'medical_office.db')
    ],
    "build_exe": "build/Cabinet Medical",
    "optimize": 2,
    "include_msvcr": True,
    "zip_include_packages": "*",
    "zip_exclude_packages": EXCLUDES,
    "silent": True,
    "bin_excludes": ["tcl86t.dll", "tk86t.dll"],
    "bin_path_excludes": ["tcl8.6/tzdata/", "tcl8.6/demos/", "tcl8.6/msgs/"],
    "bin_path_includes": TCL_REQUIRED,
    "zip_exclude_packages": EXCLUDES + ["tcl", "tcl8", "tk", "tk8"]
}

MSI_OPTIONS = {
    "upgrade_code": "{1c17c8d8-f6c5-4a4e-b44e-1e04c903c604}",
    "initial_target_dir": rf"[ProgramFilesFolder]\{__app_name__}",
    "all_users": True
}
