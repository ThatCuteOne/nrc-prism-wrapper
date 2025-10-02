import asyncio
from dataclasses import dataclass
import hashlib
import json
import logging
import os

import duckdb
import config
from pathlib import Path
from urllib.parse import urljoin
import networking.api as api
logger = logging.getLogger("Jars Geatherer")


@dataclass
class ModEntry():
    hash_md4 : str
    version : str
    ID : str
    filename : str
    old_file : str|None
    source_type : str
    repositoryRef : str
    groupId : str
    modrinth_id : str
    maven_id :str
    modrinth_slug:str

async def calc_hash(file:Path):
    '''
    Calculates the md5 hash for given path
    
    Args:
        file: path to a file
    '''
    with open(file,'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

async def get_mc_version():
    '''
    Reads the installed Minecraft Version for the current instance

    Returns:
        minecraft_version:str
    '''
    if config.LAUNCHER == "prism":
        with open("../mmc-pack.json") as f:
            mmc_pack = json.load(f)
            for component in mmc_pack.get("components"):
                if component.get("uid") == "net.minecraft":
                    return component.get("version")
    else:
        try:
            data = duckdb.connect(config.DATA_DIR/ "app.db",read_only=True)
            current_dir_name = Path(os.getcwd()).name
            data = data.sql(f"SELECT game_version FROM profiles WHERE path = '{current_dir_name}'").fetchall()
            return data[0][0]
        except Exception as e:
            raise Exception(e)
    

async def download_jar(url,filename,version:str,ID:str, old_file=None):
    '''
    Downloads a jar file from given url

    Args:
        url:str | download url
        filename:str | name of the downloaded file
        version:str | version that will be installed
        ID:str | mod ID

    Optional:
        old_file=None| old file to delete
    
    Returns:
        index_entry:dict | a dict in the format of the index
    '''
    if await api.download_jar(url,filename):
        if filename != old_file and old_file is not None:
            logger.info(f"Deleting {old_file}")
            os.remove(f"./mods/{old_file}")

        # stuffs thats written to index
        return {
            "id": ID,
            "hash": await calc_hash(f"./mods/{filename}"),
            "version": version
        }


async def read_index():
    '''
    Reads installed versions index

    Returns:
        index_data:list
    '''
    try:
        with open(".nrc-index.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

async def get_installed_versions():
    '''
    Scans the mod dir for installed mods and links them to thier index entry

    Returns
        result:dict
    '''

    index = await read_index()
    hashes = {}
    files = os.scandir("./mods")
    for f in files:
        if f.name.endswith(".jar") or f.name.endswith(".jar.disabled"):
            hashes[await calc_hash(f)] = {
                "filename" : f.name
            }

    result = {}
    for entry in index:
        if entry.get("hash") in hashes:
            result[entry.get("id")] = {
                "version": entry.get("version"),
                "filename": hashes.get(entry.get("hash")).get("filename"),
                "hash":entry.get("hash")
            }
    return result


async def get_compatible_nrc_mods(mc_version,mods:list):
    '''
    Gets mods from norisk api and Filters them for compatibility with given mc_version

    Args:
        mc_version:str
        mods:list

    Returns:
        mods:list| compatible mods
    '''
    retrun_mods = []
    for mod in mods:
        if mod.get("compatibility").get(mc_version):
                if mod.get("compatibility").get(mc_version).get("fabric").get("source"):
                    source = mod.get("compatibility").get(mc_version).get("fabric").get("source")
                else:
                    source = mod.get("source")
                if source.get("type") == "modrinth":
                    retrun_mods.append(
                        ModEntry(
                            None, # hash
                            mod.get("compatibility").get(mc_version).get("fabric").get("identifier"), # version
                            mod.get("id"), # ID
                            None, # filename
                            None, # old_file
                            source.get("type"), # source type
                            source.get("repositoryRef"),
                            source.get("groupId"),
                            source.get("projectId"),
                            source.get("artifactId"),
                            source.get("projectSlug")
                        )
                    )
                else:
                    retrun_mods.append(
                        ModEntry(
                            None, # hash
                            mod.get("compatibility").get(mc_version).get("fabric").get("identifier"), # version
                            mod.get("id"), # ID
                            None, # filename
                            None, # old_file
                            source.get("type"), # source type
                            source.get("repositoryRef"),
                            source.get("groupId"),
                            source.get("projectId"),
                            source.get("artifactId"),
                            None
                        )
                    )
    return retrun_mods


async def remove_installed_mods(mods:list[ModEntry],installed_mods:dict) -> tuple[list[ModEntry],list[ModEntry]]:
    '''
    Removes already installed mods form modlist

    Args:
        mods: Remote mods
        installed_mods
    '''
    result = []
    removed = []
    for mod in mods:
        if mod.ID in installed_mods:
            if mod.version != installed_mods[mod.ID].get("version"):
                logger.info(f"Version mismatch detected installed:{installed_mods[mod.ID].get("version")} Remote Version:{mod.version}")
                mod.old_file = installed_mods[mod.ID].get("filename")
                result.append(mod)
            else:
                mod.hash_md4 = installed_mods[mod.ID].get("hash")
                removed.append(mod)
        else:
            result.append(mod)
    return result , removed

async def write_to_index_file(data:list):
    '''
    Writes data to  ".nrc-index.json" index file
    '''
    with open(".nrc-index.json","w") as f:
        json.dump(data,f,indent=2)

async def build_modrinth_maven_url(artifact:ModEntry):
    '''
    builds maven url from ModEntry

    Args:
        artifact:ModEntry
        repos: repository refrences
    Returns:
        url:download uil
        filename: name of the file
    '''
    
    # this works for all
    # filename = f"{artifact.modrinth_slug}-{artifact.version}.jar"
    # artifact_path = f"maven/modrinth/{artifact.ID}/{artifact.version}/{filename}"
    filename = f"{artifact.modrinth_slug}-{artifact.version}.jar"
    artifact_path = f"maven/modrinth/{artifact.ID}/{artifact.version}/{filename}"
    return urljoin("https://api.modrinth.com/maven/", artifact_path),filename




async def build_maven_url(artifact:ModEntry,repos):
    '''
    builds maven url from ModEntry

    Args:
        artifact:ModEntry
        repos: repository refrences
    Returns:
        url:download uil
        filename: name of the file
    '''

    group_path = artifact.groupId.replace('.', '/')
    
    filename = f"{artifact.maven_id}-{artifact.version}.jar"
    artifact_path = f"{group_path}/{artifact.maven_id}/{artifact.version}/{filename}"
    return urljoin(repos.get(artifact.repositoryRef), artifact_path),filename

async def convert_to_index(mods:list[ModEntry]):
        '''
        Converts ModEntrys to index format
        '''
        result = []
        for mod in mods:
            result.append({
                "id": mod.ID,
                "hash": mod.hash_md4,
                "version": mod.version
            })
        return result

def filter_none(items):
    return [item for item in items if item is not None] if items else []


async def main(remote_mods:list,repos):
    '''
    Verifys and installs mod jars
    '''
    mc_version = await get_mc_version()
    logger.info("getting jars")
    mods = await get_compatible_nrc_mods(mc_version,remote_mods)
    installed_mods = await get_installed_versions()
    mods, removed = await remove_installed_mods(mods,installed_mods)
    download_tasks = []
    for mod in mods:
        if mod.source_type == "modrinth":
            url,filename = await build_modrinth_maven_url(mod)
            download_tasks.append(download_jar(url,filename,mod.version,mod.ID,mod.old_file)) 
        elif mod.source_type == "maven":
                url,filename = await build_maven_url(mod,repos)
                download_tasks.append(download_jar(url,filename,mod.version,mod.ID,mod.old_file)) 

    if download_tasks:
        logger.info("Downloading jars")
        existing_mods_index = await convert_to_index(removed)
        index = await asyncio.gather(*download_tasks)
        await write_to_index_file(filter_none(index) + filter_none(existing_mods_index))
    else:
        logger.info("No Jars need to be downloaded")

