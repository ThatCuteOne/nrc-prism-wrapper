#!/usr/bin/env python3
import subprocess
import config
from networking import api
from tasks import jars
import tasks.get_dependencies as get_dependencies
import logging
import asyncio
import os
import sys
from shutil import which
import tasks.get_token as get_token
import tasks.get_assets as get_assets


logging.basicConfig(level=logging.INFO,format='[%(asctime)s] [%(name)s/%(levelname)s] %(message)s',datefmt='%H:%M:%S')
get_dependencies.check_dependencies()

logger = logging.getLogger("NRC Wrapper")



# Wrapper script for the NoRisk Client.
# This script adds the -D property, downloads assets, mods and then runs the game start command.

os.makedirs("./mods",exist_ok=True)

ASSET_PATH = "NoRiskClient/assets"
def remove_duplicates_by_keys(dict_list, keys):
    seen = set()
    unique_dicts = []
    
    for d in dict_list:
        # Create a tuple of values for the specified keys
        key_tuple = tuple(d[key] for key in keys)
        if key_tuple not in seen:
            seen.add(key_tuple)
            unique_dicts.append(d)
    
    return unique_dicts

async def download_data():
    versions = await api.get_norisk_versions()
    pack =versions.get("packs").get(config.NORISK_PACK)
    repos = versions.get("repositories")
    mods, assets = await get_data(pack,versions)
    tasks =[
        get_assets.main(assets),
        jars.main(remove_duplicates_by_keys(mods,["id"]),repos),
        get_token.main()

    ]
    results = await asyncio.gather(*tasks)
    for result in results:
        if result is not None:
            return result



async def get_data(pack,versions):
    '''
    returns a list of all remote mods and asset-packs that need to be installed
    '''  
    def filter_none(items):
        return [item for item in items if item is not None] if items else []

    mods:list = pack.get("mods",[])
    assets:list = pack.get("assets",[])
    inheritsFrom = pack.get("inheritsFrom")
    if inheritsFrom is None:
        inheritsFrom = []
    for parent_pack_name in inheritsFrom:
        parent_pack = versions.get("packs",[]).get(parent_pack_name)
        if not parent_pack:
            continue
        assets.extend(parent_pack.get("assets",[]))
        mods.extend(parent_pack.get("mods",[]))
        inherited_mods,inherited_assets = await get_data(parent_pack, versions)
        mods.extend(inherited_mods)
        assets.extend(inherited_assets)

    return filter_none(mods),filter_none(assets)




def main():
    token = asyncio.run(download_data())
    asyncio.run(get_assets.injectIntoJar())

    # Get the original command arguments
    original_args = config.unknown_args

    if which('obs-gamecapture') is not None:
        new_cmd = ["obs-gamecapture"]
    else:
        new_cmd = []

    token_added = False

    for arg in original_args:
        new_cmd.append(arg)
        # When we find the Java executable or main class, inject our token arg
        if (arg.endswith('java') or
            arg == 'net.minecraft.client.main.Main' or
            arg.endswith('/java') or
            arg.endswith('\\java.exe') or
            arg.endswith('javaw.exe')) and not token_added:
            new_cmd.append(f"-Dnorisk.token={token}")
            token_added = True

    if not token_added:
        new_cmd.append(f"-Dnorisk.token={token}")
    try:
        # windows log output workaround(i hate you billie)
        # TODO for some reason the log reading is very slow and wierd but at least it works
        if sys.platform == "win32":
            logger.warning("Using Windows log stream workaround... the log may be slow")
            process = subprocess.Popen(
                new_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            sys.exit(process.returncode)
        else:
            logger.info("Starting Minecraft..")
            os.execvp(new_cmd[0], new_cmd)
    except FileNotFoundError:
        print(f"ERROR: Command not found: {new_cmd[0]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to execute command: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
