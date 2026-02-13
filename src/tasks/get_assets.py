import asyncio
from dataclasses import dataclass
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
os.makedirs(ASSET_PATH,exist_ok=True)


#TODO/CHORE expose this as setting
concurrent_downloads = 20

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

@dataclass
class Assetfile():
    path : str
    sha : str
    asset_id : str
    size : int
    is_verified = False

    async def verify(self):
        file_path = Path(f"{ASSET_PATH}/{self.path}")
        if file_path.is_file():
            local_hash = await calc_hash(file_path)
            if not local_hash == self.sha:
                self.is_verified = False
                return False
        else:
            self.is_verified = False
            return False
        self.is_verified = True
        return True

    async def download(self,semaphore:asyncio.Semaphore=asyncio.Semaphore(10)):
        url = f"https://cdn.norisk.gg/assets/{self.asset_id}/assets/{self.path}"
        await api.download_file(url,f"{ASSET_PATH}/{self.path}",semaphore,target_hash=self.sha)

    
async def run(asset_packs):
    assets = list(set(asset_packs))

    # get metadata
    tasks = []
    meta_data: dict[str, dict[str,Assetfile]] = {}

    for a in assets:
        tasks.append(get_metadata(a,meta_data))
    await asyncio.gather(*tasks)
    assets.reverse()

    master_assets:dict[str, Assetfile] = {}

    # flatten asset tree
    for assetpack in assets:
        for id, resource in meta_data[assetpack].items():
            master_assets[resource.path] = resource


    download_tasks = []
    semaphore = asyncio.Semaphore(concurrent_downloads)
    for path, resource in master_assets.items():
        if await resource.verify() or path in IGNORE_LIST: 
            continue
        download_tasks.append(resource.download(semaphore=semaphore))
    
    await asyncio.gather(*download_tasks)
    

async def get_metadata(asset_pack_name:str,metadata_dict:dict):
    raw_metadata:dict = (await api.get_asset_metadata(asset_pack_name)).get("objects")
    metadata_dict[asset_pack_name] = {}
    for path, data in raw_metadata.items():
        metadata_dict[asset_pack_name][path] = Assetfile(
            path=path,
            sha=data.get("hash",None),
            asset_id=asset_pack_name,
            size=data.get("size",1)
        )