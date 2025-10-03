
import argparse
import json
import os
from pathlib import Path
import logging
import duckdb

def get_mc_version()-> str:
    '''
    Reads the installed Minecraft Version for the current instance

    Returns:
        minecraft_version:str
    '''
    if LAUNCHER == "prism":
        with open("../mmc-pack.json") as f:
            mmc_pack = json.load(f)
            for component in mmc_pack.get("components"):
                if component.get("uid") == "net.minecraft":
                    return component.get("version")
    else:
        try:
            data = duckdb.connect(DATA_DIR/ "app.db",read_only=True)
            current_dir_name = Path(os.getcwd()).name
            data = data.sql(f"SELECT game_version FROM profiles WHERE path = '{current_dir_name}'").fetchall()
            return data[0][0]
        except Exception as e:
            raise Exception(e)

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


MINECRAFT_VERSION = get_mc_version()