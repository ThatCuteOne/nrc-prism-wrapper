from importlib.machinery import SourceFileLoader
import os
from pathlib import Path
import subprocess
import sys
import logging
import tempfile
logger = logging.getLogger("Dependency Checker")



filename = Path(__file__)
loader:SourceFileLoader = getattr(sys.modules['__main__'], '__loader__', None)
meow = loader.get_data("requirements.txt").decode('utf-8')

with tempfile.NamedTemporaryFile("w",delete=False) as f:
    try:
        f.write(meow)
        f.flush()
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", f.name])
        f.close()
    except:
        os.remove(f.name)
    finally:
        os.remove(f.name)