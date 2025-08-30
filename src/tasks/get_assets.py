import asyncio
import hashlib
import logging
import os
from pathlib import Path
from aiofiles import os as aios
import aiofiles
import networking.api as api
import config

logger = logging.getLogger("Assets")

IGNORE_LIST = []

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

async def copy_dir(src,dst):
    items = await aios.listdir(src)
    copy_tasks = []
    for item in items:
        if not item == "pack.mcmeta":
            source_path = os.path.join(src,item)
            destination_path = os.path.join(dst,item)
            if await aios.path.isdir(source_path):
                copy_tasks.append(copy_dir(source_path, destination_path))
            else:
                copy_tasks.append(copy_file(source_path, destination_path))

    await asyncio.gather(*copy_tasks)


async def copy_file(src,dst):
    dst_dir = os.path.dirname(dst)
    if not await aios.path.exists(dst_dir):
        await aios.makedirs(dst_dir, exist_ok=True)
    
    async with aiofiles.open(src, 'rb') as src_file:
        async with aiofiles.open(dst, 'wb') as dst_file:
            content = await src_file.read()
            await dst_file.write(content)
async def main(nrc_token:str):
    '''
    Verifys and Downloads Assets

    Args:
        nrc_token: a valid noriskclient token
    '''
    logger.info("Verifying Assets")
    metadata = await api.get_asset_metadata("norisk-prod")
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
        task = api.download_single_asset("norisk-prod",path,asset_data,nrc_token,semaphore)
        tasks.append(task)
    logger.info("Downloading missing")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    if config.ASSET_OVERRIDE:
        # TODO make load order deterministic
        for d in os.listdir("nrc_asset_overrides"):
             path = Path(f"nrc_asset_overrides/{d}")
             if path.is_dir():
                 if Path(path/"pack.mcmeta").exists():
                     logger.info(f"Loading asset pack: {d}")
                     await copy_dir(Path(f"nrc_asset_overrides/{d}"),"NoRiskClient")