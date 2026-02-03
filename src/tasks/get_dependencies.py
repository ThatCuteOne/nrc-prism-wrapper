from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess
import sys
import logging
import tempfile
logger = logging.getLogger("Dependency Checker")



filename = Path(__file__)
loader:SourceFileLoader = getattr(sys.modules['__main__'], '__loader__', None)
meow = loader.get_data("requirements.txt").decode('utf-8')

with tempfile.NamedTemporaryFile("w") as f:
    f.write(meow)
    f.flush()
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", f.name])