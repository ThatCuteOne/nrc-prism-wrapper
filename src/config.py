
import argparse
import json
import os
from pathlib import Path
import logging
import duckdb

def get_instance_data()-> tuple[str,str,str]:
    '''
    Reads the installed Minecraft Version for the current instance

    Returns:
        tuple[minecraft_version,mod_loader,mod_loader_version]
    '''
    minecraft_version : str
    loader: str
    loader_version:str

    if LAUNCHER == "prism":
        with open("../mmc-pack.json") as f:
            mmc_pack = json.load(f)
            for component in mmc_pack.get("components"):
                if component.get("uid") == "net.minecraft":
                    minecraft_version = component.get("version")
                if component.get("uid") == "net.fabricmc.fabric-loader":
                    loader = "fabric"
                    loader_version = component.get("version")
                elif component.get("uid") == "net.neoforged":
                    loader = "neoforge" 
                    loader_version = component.get("version")
                elif component.get("uid") == "net.minecraftforge":
                    loader = "forge" 
                    loader_version = component.get("version")
                elif component.get("uid") == "net.minecraftforge":
                    loader = "forge" 
                    loader_version = component.get("version")
                elif component.get("uid") == "org.quiltmc.quilt-loader":
                    loader = "quilt" 
                    loader_version = component.get("version")
        return minecraft_version,loader,loader_version
    else:
        try:
            data = duckdb.connect(DATA_DIR/ "app.db",read_only=True)
            current_dir_name = Path(os.getcwd()).name
            result = data.sql(f"SELECT mod_loader, mod_loader_version, game_version FROM profiles WHERE path = '{current_dir_name}'").fetchall()
            if result:
                mod_loader, mod_loader_version, game_version = result[0]
                return game_version,mod_loader, mod_loader_version
            else:
                raise Exception(f"No profile found for path: {current_dir_name} in database")
        except Exception as e:
            raise Exception(e)

os.makedirs("nrc_asset_overrides",exist_ok=True)

logger = logging.getLogger("Config")

parser = argparse.ArgumentParser(description='NRC Wrapper for third party launchers')
parser.add_argument("-l","--launcher", type=str,help="Overrides the automatic launcher detection\nOptions: prism | modrinth")
parser.add_argument("--modrinth-data-path",type=str,default="../../",help="path to the dir that contains app.db")
parser.add_argument("--prism-data-path",type=str,default="../../..",help="path to the dir that contains accounts.json")
parser.add_argument("-p","--norisk-pack",type=str,default="norisk-prod",help="Norisk pack to use:\n Avaliable Norisk packs: \"norisk-bughunter\", \"norisk-dev\" \"hypixel-skyblock\",\"mazerunner\", \"stupid-mod-ideas\", \"hide-and-seek\"")
parser.add_argument("-m","--mc-version", type=str,help="Overrides the automatic minecraft version detection")


args, unknown_args = parser.parse_known_args()

LAUNCHER = args.launcher
MODRINTH_DATA_DIR = args.modrinth_data_path
PRISM_DATA_DIR = args.prism_data_path
NORISK_PACK = args.norisk_pack
MINECRAFT_VERSION, LOADER, LOADER_VERSION = get_instance_data()

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

if args.mc_version is not None:
    MINECRAFT_VERSION = args.mc_version