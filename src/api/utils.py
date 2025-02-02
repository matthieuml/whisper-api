import mimetypes
import os
import time
from urllib.parse import urlparse

import requests
from werkzeug.utils import secure_filename


def allowed_extensions(filename: str, allowed_extensions: set) -> bool:
    """Check if the file has an allowed extension"""
    if not isinstance(allowed_extensions, set):
        raise ValueError("Invalid allowed_extensions")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def download_file(url: str, upload_folder: str, allowed_domains=set()) -> str:
    """Download file from URL and save it to upload folder"""
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL")

        # Validate allowed domains
        if not isinstance(allowed_domains, set):
            raise ValueError("Invalid allowed_domains")
        if "*" not in allowed_domains and parsed_url.netloc not in allowed_domains:
            raise ValueError("Domain not allowed")

        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Try to get filename from URL or Content-Disposition header
        content_disposition = response.headers.get("content-disposition")
        if content_disposition and "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[1].strip("\"'")
        else:
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                # If no filename in URL, try to guess extension from content-type
                content_type = response.headers.get("content-type", "")
                ext = mimetypes.guess_extension(content_type) or ".audio"
                filename = f"audio{ext}"

        # Add timestamp and secure the filename
        timestamp = str(int(time.time()))
        filename_with_timestamp = f"{timestamp}-{secure_filename(filename)}"
        file_path = os.path.join(upload_folder, filename_with_timestamp)

        # Save the file
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return file_path
    except Exception as e:
        raise ValueError(f"Failed to download file from URL: {str(e)}")
