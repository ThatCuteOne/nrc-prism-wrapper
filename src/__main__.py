#!/usr/bin/env python3
import tasks.get_dependencies  # noqa: F401
import subprocess
import config
from networking import api
from tasks import jars
import logging
import asyncio
import os
import sys
from shutil import which
import tasks.get_token as get_token
import tasks.get_assets as get_assets

# if you want to debug the modrinth app
# handlers={
#     logging.FileHandler('./modrinth-wrapper.log',encoding="utf-8"),
#     logging.StreamHandler()
# }                                                                                                                  put it here
logging.basicConfig(level=logging.INFO,format='[%(asctime)s] [%(name)s/%(levelname)s] %(message)s',datefmt='%H:%M:%S')

logger = logging.getLogger("NRC Wrapper")



# Wrapper script for the NoRisk Client.
# This script adds the -D property, downloads assets, mods and then runs the game start command.

os.makedirs(config.NRC_MOD_PATH,exist_ok=True)

class ModLoader():
    def __init__(self,loader_type,version):
        self.type = loader_type
        self.version = version

class DataManager():
    def __init__(self, data):
        self.data = data
        self.mods = []
        self.assetpacks = []
        self.repos = self.data.get("repositories")
        self.compatible_versions = []
        self.loader:ModLoader = None
        self.pack = self.data.get("packs").get(config.NORISK_PACK)
        

        packs = []
        def process(pack):
            if not self.loader and pack.get("loaderPolicy").get("default").get("fabric").get("version"):
                self.loader = ModLoader("fabric",pack.get("loaderPolicy").get("default").get("fabric").get("version"))
            if pack.get("assets"):
                self.assetpacks.extend(pack.get("assets"))
            if pack.get("mods"):
                self.mods.extend(pack.get("mods"))
            if pack.get("inheritsFrom"):
                for p in pack.get("inheritsFrom"):
                    if p not in packs:
                        packs.append(p)
                        process(self.data.get("packs").get(p))
        
        process(self.pack)
        self.assetpacks = list(set(self.assetpacks))
        filtered_mods = []
        filtered_ids = []
        for m in self.mods:
            if m.get("id") in filtered_ids:
                continue
            else:
                self.compatible_versions.extend(m.get("compatibility"))
                filtered_ids.append(m.get("id"))
                filtered_mods.append(m)
        self.mods = filtered_mods
        self.compatible_versions = list(set(self.compatible_versions))
        


ASSET_PATH = "NoRiskClient/assets"

async def validate(data:DataManager):
    if config.MINECRAFT_VERSION in data.compatible_versions:
        if data.loader:
            if data.loader.type == config.LOADER:
                if not data.loader.version == config.LOADER_VERSION:
                    logger.warning(f"You are using a version of the modloader that isnt recommended. The recommended loader version is \"{data.loader.version}\" but the wrong version is present \"{config.LOADER_VERSION}\"!!")
            else:
                logger.error(f"Pack \"{data.pack.get("displayName")}\" isnt compatible with \"{config.LOADER}\"\nPlease Install \"{data.loader.type}\" version:\"{data.loader.version}\"")
                sys.exit(1)
    else:
        logger.error(f"Pack \"{data.pack.get("displayName")}\" isnt compatible with \"{config.MINECRAFT_VERSION}\"\nAvalible versions for this pack: {data.compatible_versions}")
        sys.exit(1)


async def download_data():
    modpacks = await api.get_norisk_modpacks()
    if config.NORISK_PACK not in modpacks.get("packs"):
        logger.error(f"{config.NORISK_PACK} isnt a valid modpack id. Valid ids are: {list(modpacks.get("packs").keys())}")
        sys.exit(1)
    data = DataManager(modpacks)
    await validate(data)
    tasks =[
        get_assets.run(data.assetpacks),
        jars.main(data.mods,data.repos),
        get_token.main()

    ]
    results = await asyncio.gather(*tasks)
    for result in results:
        if result is not None:
            return result



def main():
    token = asyncio.run(download_data())
    asyncio.run(get_assets.injectIntoJar())

    # Get the original command arguments
    original_args = config.unknown_args

    if which('obs-gamecapture') is not None:
        new_cmd = ["obs-gamecapture"]
    else:
        new_cmd = []

    new_cmd.append(original_args[0])
    new_cmd.append(f"-Dnorisk.token={token}")
    new_cmd.append(f"-Dfabric.addMods={config.NRC_MOD_PATH}")
    new_cmd.extend(original_args[1:])


    try:
        logger.info("Starting Minecraft..")
        if sys.platform == "win32":
            # windows log output workaround(i hate you billie)
            new_cmd[0] = new_cmd[0].replace("javaw.exe","java.exe")
            subprocess.run(new_cmd)
        else:
            os.execvp(new_cmd[0], new_cmd)
    except FileNotFoundError:
        print(f"ERROR: Command not found: {new_cmd[0]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to execute command: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
