#!/usr/bin/env python3
import subprocess
import config
from networking import api
import tasks.get_dependencies as get_dependencies
import logging
import asyncio
import os
import sys
from shutil import which
import tasks.get_token as get_token
import tasks.get_assets as get_assets
import tasks.install_norisk_version as install_norisk_version


logging.basicConfig(level=logging.INFO,format='[%(asctime)s] [%(name)s/%(levelname)s] %(message)s',datefmt='%H:%M:%S')
get_dependencies.check_dependencies()

logger = logging.getLogger("NRC Wrapper")



# Wrapper script for the NoRisk instance.
# Prism Launcher will call this script with the original Java command as arguments.
# This script adds the -D property, downloads assets, mods and then runs the command.

os.makedirs("./mods",exist_ok=True)

ASSET_PATH = "NoRiskClient/assets"

async def download_data():
    versions = await api.get_norisk_versions()
    pack =versions.get("packs").get(config.NORISK_PACK)
    repos = versions.get("repositories")
    tasks =[
        get_assets.main(pack),
        install_norisk_version.main(pack,repos),
        get_token.main()

    ]
    results = await asyncio.gather(*tasks)
    for result in results:
        if result is not None:
            return result
    

def main():
    #token = asyncio.run(get_token.main())
    # if not token:
    #     logger.exception("ERROR: Missing Norisk token")
    #     sys.exit(1)

    token = asyncio.run(download_data())
    asyncio.run(get_assets.injectIntoJar())

    # Get the original command arguments
    original_args = sys.argv[1:]
    
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
