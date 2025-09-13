
import argparse
import os
from pathlib import Path
import logging
os.makedirs("nrc_asset_overrides",exist_ok=True)

logger = logging.getLogger("Config")

parser = argparse.ArgumentParser(description='NRC Wrapper for third party launchers')
parser.add_argument("-l","--launcher", type=str,help="Overrides the automatic launcher detection\nOptions: prism | modrinth")
parser.add_argument("--modrinth-data-path",type=str,default="../../",help="path to the dir that contains app.db")
parser.add_argument("--prism-data-path",type=str,default="../../..",help="path to the dir that contains accounts.json")
parser.add_argument("-p","--norisk-pack",type=str,default="norisk-prod",help="Norisk pack to use:\n Avaliable Norisk packs: \"norisk-bughunter\", \"norisk-dev\" \"hypixel-skyblock\",\"mazerunner\", \"stupid-mod-ideas\", \"hide-and-seek\"")

args, unknown_args = parser.parse_known_args()

LAUNCHER = args.launcher
MODRINTH_DATA_DIR = args.modrinth_data_path
PRISM_DATA_DIR = args.prism_data_path
NORISK_PACK = args.norisk_pack

if LAUNCHER is None:
    if Path(MODRINTH_DATA_DIR + "/app.db").is_file():
        LAUNCHER = "modrinth"
        logger.info("Detetected Modrinth Launcher")
    else:
        LAUNCHER = "prism"
        logger.info("Detetected Prism Launcher")
if LAUNCHER == "modrinth":
    DATA_DIR = MODRINTH_DATA_DIR
elif LAUNCHER == "prism":
    DATA_DIR = PRISM_DATA_DIR
else:
    raise Exception("Invalid Launcher type")