"""
vidinie stock image utilities module
utility functions for fetching stock images from unsplash and pexels apis.
"""

import os
import requests
from typing import Optional, Dict
import hashlib
from utils.logger import get_logger

logger = get_logger(__name__)


def fetch_from_unsplash(query: str, api_key: str, output_dir: str) -> Optional[Dict]:
    """
    fetch image from unsplash.
    args:
        query: search query
        api_key: unsplash api access key
        output_dir: directory to save images
    returns:
        image metadata or None if failed
    """
    try:
        unsplash_base_url = "https://api.unsplash.com"
        
        # search for images
        search_url = f"{unsplash_base_url}/search/photos"
        headers = {
            "Authorization": f"Client-ID {api_key}"
        }
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('results'):
            logger.warning(f"No Unsplash results for query: {query}")
            return None
        
        photo = data['results'][0]
        
        # download image
        image_url = photo['urls']['regular']  # 1080px wide
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        # generate filename
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        filename = f"unsplash_{query_hash}_{photo['id']}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        # save image
        with open(filepath, 'wb') as f:
            f.write(image_response.content)
        
        logger.info(f"Downloaded Unsplash image for '{query}': {filename}")
        
        # trigger download tracking (unsplash api requirement)
        if photo.get('links', {}).get('download_location'):
            try:
                requests.get(
                    photo['links']['download_location'],
                    headers=headers
                )
            except:
                pass
        
        return {
            'filename': filename,
            'filepath': filepath,
            'source': 'unsplash',
            'query': query,
            'url': photo['urls']['regular'],
            'photographer': photo['user']['name'],
            'photographer_url': photo['user']['links']['html'],
            'photo_url': photo['links']['html'],
            'width': photo['width'],
            'height': photo['height'],
            'description': photo.get('description', ''),
            'alt_description': photo.get('alt_description', '')
        }
        
    except Exception as e:
        logger.error(f"Error fetching from Unsplash: {str(e)}")
        return None


def fetch_from_pexels(query: str, api_key: str, output_dir: str) -> Optional[Dict]:
    """
    fetch image from pexels.
    args:
        query: search query
        api_key: pexels api key
        output_dir: directory to save images
    returns:
        image metadata or None if failed
    """
    try:
        pexels_base_url = "https://api.pexels.com/v1"
        
        # search for images
        search_url = f"{pexels_base_url}/search"
        headers = {
            "Authorization": api_key
        }
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('photos'):
            logger.warning(f"No Pexels results for query: {query}")
            return None
        
        photo = data['photos'][0]
        
        # download image (use large size)
        image_url = photo['src']['large']  # 940px wide
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        # generate filename
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        filename = f"pexels_{query_hash}_{photo['id']}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        # save image
        with open(filepath, 'wb') as f:
            f.write(image_response.content)
        
        logger.info(f"Downloaded Pexels image for '{query}': {filename}")
        
        return {
            'filename': filename,
            'filepath': filepath,
            'source': 'pexels',
            'query': query,
            'url': photo['src']['large'],
            'photographer': photo['photographer'],
            'photographer_url': photo['photographer_url'],
            'photo_url': photo['url'],
            'width': photo['width'],
            'height': photo['height'],
            'description': photo.get('alt', ''),
            'alt_description': photo.get('alt', '')
        }
        
    except Exception as e:
        logger.error(f"Error fetching from Pexels: {str(e)}")
        return None

