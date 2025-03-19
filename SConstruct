# SConstruct file for a single example.
#
# Usage: `scons BUILD_TYPE=debug` will build debug version, `scons` will build release version.

# Call the generic `SConstructGeneral` script that will configure everything. It is located at the top level directory of opendihu.
# That script will then call a `SConscript` file that defines which sources to use.

import os

# get the directory where opendihu is installed (the top level directory of opendihu)
opendihu_home = os.environ.get('OPENDIHU_HOME') or "../../../../../../"

# set path where the "SConscript" file is located (set to current path)
path_where_to_call_sconscript = Dir('.').srcnode().abspath

# call general SConstruct that will configure everything and then call SConscript at the given path
SConscript(os.path.join(opendihu_home,'SConstructGeneral'),
           exports={"path": path_where_to_call_sconscript})
