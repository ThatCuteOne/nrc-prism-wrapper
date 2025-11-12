import asyncio
import hashlib
import json
import logging
import os
import zipfile
from pathlib import Path
import config
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

    mods_dir = Path(config.NRC_MOD_PATH)
    target_hash = core_mod.get("hash")
    
    for file in mods_dir.glob("*.jar"):
        if await calc_hash(file) == target_hash:
            temp_jar_path = file.with_suffix('.temp.jar')
            
            try:
                with zipfile.ZipFile(file, 'r') as original_jar:
                    with zipfile.ZipFile(temp_jar_path, 'w', compression=zipfile.ZIP_DEFLATED) as updated_jar:
                        logger.info("Updating JAR file")
                        
                        assets_to_replace = {jar_path for _, jar_path in files_to_add}
                        for item in original_jar.infolist():
                            if item.filename not in assets_to_replace:
                                updated_jar.writestr(item, original_jar.read(item.filename))
                        
                        for file_path, jar_path in files_to_add:
                            with open(file_path, 'rb') as f:
                                updated_jar.writestr(jar_path, f.read())
                
                file.unlink()
                temp_jar_path.rename(file)
                
                core_mod["hash"] = await calc_hash(file)
                with open(".nrc-index.json", 'w') as f:
                    json.dump(index, f, indent=2)
                logger.info("Successfully updated JAR file!")
                break
                
            except Exception as e:
                if temp_jar_path.exists():
                    temp_jar_path.unlink()
                logger.error(f"Error updating JAR: {e}")
                raise

async def run(asset_packs):
    assets = list(set(asset_packs))
    tasks = []
    logger.info(assets)
    for a in assets:
        tasks.append(main(a))

    await asyncio.gather(*tasks)


async def main(assetpack):
    '''
    Verifys and Downloads Assets
    '''
    
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
