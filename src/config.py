
import os
import json5
from pathlib import Path
import logging
os.makedirs("nrc_asset_overrides",exist_ok=True)

logger = logging.getLogger("Config")

WRAPPER_ROOT = (Path(__file__).resolve()).parent
default_config = '''\
{
    // allow for asset overrides via an asset pack
    "asset_overrides" : true,
    // the directory this script looks for the minecraft auth token when prism launcher is detected
    "prism_data_dir": "../../..",
    //the path to your app.db from the modrinth launcher
    "modrinth_data_dir": "../../app.db",
    //TODO DOES NOT WORK CURRENTLY(force install newest mod versions) 
    "force_newest_mods": false,
    // forces launcher type(mostly used vor development) "null" to disable
    "force_launcher_type": null
}
    '''

def get_config()-> dict:
    try:
        with open(f"{WRAPPER_ROOT.parent}/config.jsonc","r") as f:
            config = json5.load(f)
    except FileNotFoundError:
        config = json5.loads(default_config)
        with open(f"{WRAPPER_ROOT.parent}/config.jsonc","w") as f:
            f.write(default_config)


    return config

c = get_config()

LAUNCHER = c.get("force_launcher_type")
MODRINTH_DATA_PATH = c.get("modrinth_data_dir")
ASSET_OVERRIDE = c.get("asset_overrides")
PRISM_DATA_DIR = c.get("prism_data_dir")
FORCE_NEWEST_MODS = c.get("force_newest_mods")

if not LAUNCHER:
    if Path(MODRINTH_DATA_PATH).is_file():
        LAUNCHER = "modrinth"
        logger.info("Detetected Modrinth Launcher")
    else:
        LAUNCHER = "prism"
        logger.info("Detetected Prism Launcher")
