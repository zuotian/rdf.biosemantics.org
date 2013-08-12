
activate_this = '/home/ztatum/.virtualenvs/nanopub/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app as application
