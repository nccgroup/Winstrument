import os
import glob
#from SO: https://stackoverflow.com/a/1057534
modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
__all__ = [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]