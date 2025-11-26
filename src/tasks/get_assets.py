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

async def applyjarpatches():
    '''
    Injects NRC assets into nrc-core jarfile
    '''
    with open(".nrc-index.json") as f:
        index = json.load(f)

    async def patch_jar(mod:dict,file):
        temp_jar_path = file.with_suffix('.temp.jar')
        try:
            with zipfile.ZipFile(file, 'r') as original_jar:
                with zipfile.ZipFile(temp_jar_path, 'w') as updated_jar:
                    original_files = original_jar.namelist()
                    # asset injection
                    if mod.get("id") == "nrc-client":
                        source_path = Path("NoRiskClient/assets/nrc-cosmetics/assets")
                        for file_path in source_path.rglob('*'):
                            if file_path.is_file():
                                in_jar_path = f"assets/{file_path.relative_to(source_path)}"
                                updated_jar.write(file_path,in_jar_path)
                                try:
                                    original_files.remove(in_jar_path)
                                except ValueError:
                                    pass
                    for f in original_files:
                        if f == "fabric.mod.json" and mod.get("id") != "nrc-client": # patch fabric.mod.json
                            with original_jar.open(f) as jsonfile:
                                json_data = json.load(jsonfile)
                                if json_data.get("custom",None) is None:
                                    json_data["custom"] = {
                                        "modmenu":{
                                            "parent":{
                                                "id" : "nrc-client"
                                            }
                                        }
                                    }
                                elif json_data["custom"].get("modmenu",None) is None:
                                    json_data["custom"]["modmenu"] = {
                                        "parent" : {
                                            "id": "nrc-client"
                                        }
                                    }
                                else:
                                    if json_data["custom"]["modmenu"].get("parent",None) is None:
                                        json_data["custom"]["modmenu"]["parent"] = {
                                            "id": "nrc-client"
                                        }

                                updated_jar.writestr("fabric.mod.json", json.dumps(json_data, indent=2))

                            continue
                        else:
                            # copy original data 
                            data = original_jar.read(f)
                            updated_jar.writestr(f, data)
                        
                    original_jar.close()
                    updated_jar.close()
                    os.replace(temp_jar_path,file)
                    mod["hash"] = await calc_hash(file)
                    return mod
            
        except Exception as e:
            if temp_jar_path.exists():
                temp_jar_path.unlink()
            logger.error(f"Error updating JAR: {e}")
            raise
    logger.info("Applying jar patches..")

    mods_dir = Path(config.NRC_MOD_PATH)
    files = list(mods_dir.glob("*.jar"))
    
    nrc_jars = []
    for mod in index:
        target_hash = mod.get("hash")
        for file in files:
            if await calc_hash(file) == target_hash:
                nrc_jars.append(patch_jar(mod,file))
                files.remove(file)
                break

    new_index = await asyncio.gather(*nrc_jars)
    with open(".nrc-index.json","w") as f:
        json.dump(new_index,f)


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
