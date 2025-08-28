import aiohttp
import asyncio
from config import Config
from database import db

class ShortLink:
    def __init__(self):
        self.url = Config.SHORTLINK_URL
        self.api_key = Config.SHORTLINK_API

    async def create_short_link(self, long_url):
        """Create short link using configured shortlink service"""
        try:
            # Get current shortlink settings from database
            settings = await db.get_shortlink_settings()
            if settings:
                self.url = settings.get("url", Config.SHORTLINK_URL)
                self.api_key = settings.get("api_key", Config.SHORTLINK_API)

            # Ensure URL has protocol
            if not self.url.startswith('http'):
                self.url = f"https://{self.url}"

            # Different shortlink APIs have different formats
            if "arolinks.com" in self.url:
                return await self._arolinks_shortener(long_url)
            elif "gplinks.in" in self.url:
                return await self._gplinks_shortener(long_url)
            elif "earnl.xyz" in self.url:
                return await self._earnl_shortener(long_url)
            else:
                # Generic shortener
                return await self._generic_shortener(long_url)
        except Exception as e:
            print(f"Error creating short link: {e}")
            return long_url

    async def _arolinks_shortener(self, long_url):
        """Arolinks.com API - Fixed"""
        try:
            async with aiohttp.ClientSession() as session:
                api_url = f"{self.url}/api"
                params = {
                    "api": self.api_key,
                    "url": long_url
                }
                
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return data.get("shortenedUrl", long_url)
                        except:
                            text = await response.text()
                            if "http" in text:
                                return text.strip()
                    return long_url
        except Exception as e:
            print(f"Arolinks error: {e}")
            return long_url

    async def _gplinks_shortener(self, long_url):
        """GPLinks.in API"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api": self.api_key,
                    "url": long_url
                }
                async with session.get(f"{self.url}/api", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("shortenedUrl", long_url)
                    return long_url
        except:
            return long_url

    async def _earnl_shortener(self, long_url):
        """Earnl.xyz API"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api": self.api_key,
                    "url": long_url
                }
                async with session.get(f"{self.url}/api", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("shortenedUrl", long_url)
                    return long_url
        except:
            return long_url

    async def _generic_shortener(self, long_url):
        """Generic shortlink API"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api": self.api_key,
                    "url": long_url
                }
                async with session.get(f"{self.url}/api", params=params) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return data.get("shortenedUrl", data.get("short_url", long_url))
                        except:
                            # Some APIs return plain text
                            text = await response.text()
                            if "http" in text:
                                return text.strip()
                    return long_url
        except:
            return long_url

# Create instance to be imported
shortlink = ShortLink()
            
