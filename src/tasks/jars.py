import asyncio
from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
from urllib.parse import urljoin
import os
import config
from networking import api

logger = logging.getLogger("Mod processor")

os.makedirs("mods",exist_ok=True)

async def calc_hash(file:Path):
    '''
    Calculates the md5 hash for given path
    
    Args:
        file: path to a file
    '''
    with open(file,'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
repos : dict
local_files = {}
for f in os.scandir("./mods"):
    if f.name.endswith(".jar") or f.name.endswith(".jar.disabled"):
            with open(f,'rb') as file:
                local_files[hashlib.md5(file.read()).hexdigest()] = {
                    "filename" : f
                }

@dataclass
class MavenSource():
    repositoryRef : str
    groupId : str
    artifactId : str



@dataclass
class ModrinthSource():
    projectId : str
    projectSlug : str

@dataclass
class ModClass():
    source : ModrinthSource | MavenSource
    ID :str
    version_identifier: str
    sha = None
    newest_installed = False,
    in_index = False
    local_mod = None
    url = None
    filename = None
    download_success = False
    

    async def download(self):
        for u in self.url:
            if await api.download_jar(u,self.filename):
                if self.local_mod:
                    old_file:os.DirEntry = (local_files.get(self.local_mod.sha)).get("filename")
                    if old_file:
                        os.remove(old_file)
            
                self.sha = await calc_hash(f"mods/{self.filename}")
                self.download_success = True
                break
            else:
                continue
            


    async def build_url(self):

        if isinstance(self.source , ModrinthSource):
            filename = f"{self.source.projectId}-{self.version_identifier}.jar"
            artifact_path = f"maven/modrinth/{self.source.projectId}/{self.version_identifier}/{filename}"

            self.url = [urljoin("https://api.modrinth.com/maven/", artifact_path)]

            self.filename = f"{self.source.projectSlug}-{self.version_identifier}.jar"
            artifact_path = f"maven/modrinth/{self.source.projectSlug}/{self.version_identifier}/{self.filename}"
            self.url.append(urljoin("https://api.modrinth.com/maven/", artifact_path))

        elif isinstance(self.source , MavenSource):
            group_path = self.source.groupId.replace('.', '/')
            filename = f"{self.source.artifactId}-{self.version_identifier}.jar"
            self.filename = filename
            artifact_path = f"{group_path}/{self.source.artifactId}/{self.version_identifier}/{filename}"

            self.url = [urljoin(repos.get(self.source.repositoryRef), artifact_path)]
    
    async def process(self):
        if self.local_mod:
            if self.local_mod.version_identifier == self.version_identifier:
                #logger.info(f"No version mismatch detected skipping {self.ID}")
                self.sha = self.local_mod.sha
                self.download_success = True
                return
 
        await self.build_url()
        await self.download()


    async def serialize(self):
        return {
            "id": self.ID,
            "hash": self.sha,
            "version": self.version_identifier
        }






async def new_modclass(mod):
    mc_version = config.MINECRAFT_VERSION
    if mod.get("compatibility").get(mc_version):
        if mod.get("compatibility").get(mc_version).get("fabric").get("source"):
            source = mod.get("compatibility").get(mc_version).get("fabric").get("source")
        else:
            source = mod.get("source")
        
        if source.get("type") == "modrinth":
            source_class = ModrinthSource(
                source.get("projectId"),
                source.get("projectSlug")
            )
        else:
            source_class = MavenSource(
                source.get("repositoryRef"),
                source.get("groupId"),
                source.get("artifactId")
            )
        
        return ModClass(
            source_class,
            mod.get("id"),
            mod.get("compatibility").get(mc_version).get("fabric").get("identifier")
        )
    else:
        return None


async def write_to_index_file(data:list):
    '''
    Writes data to  ".nrc-index.json" index file
    '''
    with open(".nrc-index.json","w") as f:
        json.dump(data,f,indent=2)

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

async def index_to_modclass(index_entry):
    mod = ModClass(
        None,
        index_entry.get("id"),
        index_entry.get("version")
    )
    mod.sha = index_entry.get("hash")
    mod.in_index = True
    return mod



async def main(mods,repositories):
    global repos
    repos = repositories
    tasks = []
    # get remote modclasses
    index = await read_index()
    mod_classes = []
    for m in mods:
        mod:ModClass = await new_modclass(m)
        if mod is None:
            continue
        for index_entry in index:
            if local_files.get(index_entry.get("hash")):
                if mod.ID == index_entry.get("id"):
                    mod.local_mod = await index_to_modclass(index_entry)
                    break

        mod_classes.append(mod)
        tasks.append(mod.process())

    await asyncio.gather(*tasks)

    new_index = []
    for m in mod_classes:
        if m.download_success:
            new_index.append( await m.serialize())
    await write_to_index_file(new_index)
    


    
