import asyncio
import hashlib
import json
import logging
import os
import zipfile
from pathlib import Path
import networking.api as api

logger = logging.getLogger("Assets")

# assets that are ignored
IGNORE_LIST = ["nrc-cosmetics/pack.mcmeta"]

ASSET_PATH = "NoRiskClient/assets"


try:
    os.makedirs(ASSET_PATH,exist_ok=True)
finally:
    pass

concurrent_downloads = 20
async def verify_asset(path,data):
    file_path = Path(f"{ASSET_PATH}/{path}")
    if file_path.is_file():
        local_hash = await calc_hash(file_path)
        if not local_hash == data.get("hash"):
            return path, data
    else:
        return path, data


async def calc_hash(file:Path):
    '''
    Calculates the md5 hash for given path
    
    Args:
        file: path to a file
    '''
    with open(file,'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

async def injectIntoJar():
    '''
    Injects NRC assets into nrc-core jarfile
    '''
    logger.info("Injecting Assets into jarfile")
    with open(".nrc-index.json") as f:
        index = json.load(f)

    core_mod = next((mod for mod in index if mod.get("id") == "nrc-core"), None)
    source_path = Path("NoRiskClient/assets/nrc-cosmetics/assets")
    files_to_add = []
    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            rel_path = file_path.relative_to(source_path)
            jar_path_entry = str(Path("assets") / rel_path).replace('\\', '/')
            files_to_add.append((file_path, jar_path_entry))

    
    mods_dir = Path("./mods")
    target_hash = core_mod.get("hash")
    for file in mods_dir.glob("*.jar"):
            if await calc_hash(file) == target_hash:
                with zipfile.ZipFile(file , "w",compression=zipfile.ZIP_DEFLATED) as jar:
                    logger.info("writing")

                    file_data = []
                    for file_path, jar_path in files_to_add:
                        with open(file_path, 'rb') as f:
                            file_data.append((jar_path, f.read()))

                    for jar_path, content in file_data:
                        jar.writestr(jar_path, content)
                
                core_mod["hash"] = await calc_hash(file)
                with open(".nrc-index.json", 'w') as f:
                    json.dump(index, f, indent=2)
                logger.info("done Writing!")
                break

async def main(nrc_pack:dict):
    '''
    Verifys and Downloads Assets
    '''
    
    for assetpack in nrc_pack.get("assets"):
        metadata = {}
        metadata = {**metadata, **await api.get_asset_metadata(assetpack)}
        logger.info("Verifying Assets")
        verify_tasks = []
        for name, asset_info in metadata.get("objects", {}).items():
            if name not in IGNORE_LIST:
                task = verify_asset(
                    name,
                    asset_info
                )
                verify_tasks.append(task)
        results = await asyncio.gather(*verify_tasks)
        downloads = [result for result in results if result is not None]

        semaphore = asyncio.Semaphore(concurrent_downloads)
        tasks = []
        for path, asset_data in downloads:
            task = api.download_single_asset(assetpack,path,asset_data,semaphore)
            tasks.append(task)
        if tasks:
            logger.info("Downloading missing")
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.info("All assets are up to date")
