import asyncio
import hashlib
import logging
import os
from pathlib import Path
import platform
from typing import Dict
import uuid
import aiofiles
import aiohttp
import httpx


logger = logging.getLogger("Minecraft/Norisk API")

ASSET_PATH = "NoRiskClient/assets"
MOJANG_SESSION_URL = "https://sessionserver.mojang.com"
NORISK_API_URL = "https://api.norisk.gg/api/v1"
concurrent_downloads = 10

async def download_jar(download_url,filename):
    """Downloads jar file from given url"""
    logger = logging.getLogger("Mod Downloader")
    logger.info(f"Downloading {filename} [{download_url}]")
    async with asyncio.Semaphore(concurrent_downloads):
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(download_url) as response:
                    response.raise_for_status()
                    async with aiofiles.open(f"./mods/{filename}", 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                        logger.info(f"Downloaded {filename} ✅")
                        return True
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.exception(f"file not found: {download_url}")
                raise Exception(f"file not found: {download_url}")
            else:
                logger.exception(f"HTTP error: {e}")
                raise Exception(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise Exception(f"Unexpected error: {e}")


async def download_single_asset(asset_id: str, path: str, asset_info: Dict,norisk_token: str, semaphore: asyncio.Semaphore) -> None:
        """Download a single asset file"""
        logger = logging.getLogger("Asset Downloader")
        async with semaphore:
            try:
                path_obj = Path(path)
                dir_path = path_obj.parent
                os.makedirs(f"{ASSET_PATH}/{dir_path}", exist_ok=True)
                
                # Download from CDN
                url = f"https://cdn.norisk.gg/assets/{asset_id}/assets/{path}"
                headers = {"Authorization": f"Bearer {norisk_token}"}
                logger.info(f"Downloading: {path_obj.name}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.read()
                            
                            # Verify hash
                            downloaded_hash = hashlib.md5(content).hexdigest()
                            if downloaded_hash != asset_info.get("hash"):
                                raise ValueError(f"Hash mismatch for {path}")
                                
                            # Save file
                            async with aiofiles.open(f"{ASSET_PATH}/{path}", "wb") as f:
                                await f.write(content)
                                
                        else:
                            raise Exception(f"Failed to download {path}: {response.status}")
                            
            except Exception as e:
                print(f"Error downloading {path}: {e} URL:{url}")
                raise



async def get_asset_metadata(asset_id):
    url = f"https://api.norisk.gg/api/v1/launcher/pack/{asset_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                logger.info(response.status)
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to fetch assets: {response.status}")
                    return {}
        except Exception as e:
            logger.exception(f"Error fetching assets: {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error("Request timed out")
            return {}
        except aiohttp.ClientError as e:
            logger.exception(f"HTTP client error: {e}")
            return {}
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return {}

async def validate_with_norisk_api(username,server_id):
    url = f"{NORISK_API_URL}/launcher/auth/validate/v2"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                params={
                    "force": False,
                    "hwid": hashlib.md5(f"{platform.node()}{uuid.getnode()}{platform.machine()}".encode()).hexdigest(),
                    "username": username,
                    "server_id": server_id
                }
            )
            if not response.is_success:
                error_text = response.text
                logger.debug(f"failed to validate server join with norisk api: {error_text}")
                raise Exception(f"failed to validate server join with norisk api: {error_text}")
            return response.json().get("value")
            
        except httpx.RequestError as e:
            logger.debug(f"API request failed: {e}")
            raise Exception(f"Norisk API request failed: {e}")


async def request_server_id():
    url = f"{NORISK_API_URL}/launcher/auth/request-server-id"
    async with httpx.AsyncClient() as client:
        logger.debug("[API]")
        
        try:
            response = await client.post(
                    url
                )
            if not response.is_success:
                error_text = response.text
                logger.debug(f"failed to get server_id from norisk api: {error_text}")
                raise Exception(f"failed to get server_id from norisk api: {error_text}")
            
            return response.json().get("serverId")
        except httpx.RequestError as e:
            logger.debug(f"Norisk API request failed: {e}")
            raise Exception(f"Norisk API request failed: {e}")


async def join_server_session(
    access_token: str,
    selected_profile: str,
    server_id: str
) -> None:
    """
    Join a Minecraft server session
    Args:
        access_token: Minecraft access token
        selected_profile: UUID of the selected profile
        server_id: Server ID to join
    """
    logger.debug(
        f"API call: join_server_session for profile: {selected_profile} server_id: {server_id}"
    )

    url = f"{MOJANG_SESSION_URL}/session/minecraft/join"
    logger.debug(f"Request URL: {url}")

    join_request = {
        "accessToken": access_token,
        "selectedProfile": selected_profile,
        "serverId": server_id
    }

    logger.debug(f"Join request - selected_profile: {selected_profile}, server_id: {server_id}")

    async with httpx.AsyncClient() as client:
        logger.debug("Sending join server request to Minecraft Session API")
        
        try:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=join_request
            )
            
            logger.debug(f"Received response with status: {response.status_code}")

            if not response.is_success:
                error_text = response.text
                logger.debug(f"Join server session failed: {error_text}")
                raise Exception(f"Failed to join server session: {error_text}")
            
            logger.debug("API call completed: join_server_session - Successfully joined server session")
            
        except httpx.RequestError as e:
            logger.debug(f"API request failed: {e}")
            raise Exception(f"Minecraft API request failed: {e}")
        

async def get_norisk_versions():
    url = f"{NORISK_API_URL}/launcher/modpacks"
    async with httpx.AsyncClient() as client:
        logger.info("Getting version profiles from norisk api")
        try:
            response = await client.get(
                url
            )
            
            if not response.is_success:
                error_text = response.text
                logger.debug(f"failed to get version profiles from norisk api: {error_text}")
                raise Exception(f"failed to get version profiles from norisk api: {error_text}")
            
            return response.json()
        except httpx.RequestError as e:
            logger.debug(f"Norisk API request failed: {e}")
            raise Exception(f"Norisk API request failed: {e}")