"""
Files service for Mattermost API operations.

This module provides high-level async methods for file-related operations
mapped to REST endpoints, returning typed models.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from ..models.base import MattermostResponse
from ..models.posts import FileInfo
from .base import BaseService


class FilesService(BaseService):
    """
    Service for file-related operations.

    Provides high-level async methods for:
    - Uploading and managing files
    - Getting file information and content
    - File thumbnails and previews
    - File metadata operations
    """

    async def upload_file(
        self,
        channel_id: str,
        file_data: bytes,
        filename: str,
        client_id: Optional[str] = None,
    ) -> List[FileInfo]:
        """
        Upload a file to a channel.

        Args:
            channel_id: Channel ID to upload to
            file_data: File content as bytes
            filename: Original filename
            client_id: Client identifier

        Returns:
            List of uploaded file information
        """
        # Note: File uploads require multipart/form-data
        form_data = {
            "channel_id": channel_id,
            "filename": filename,
        }
        if client_id:
            form_data["client_id"] = client_id

        headers = {"Content-Type": "multipart/form-data"}

        return await self._post(
            "files",
            List[FileInfo],
            data={"files": (filename, file_data)},
            headers=headers,
        )

    async def upload_files(
        self,
        channel_id: str,
        files: List[Tuple[str, bytes]],  # List of (filename, file_data) tuples
        client_id: Optional[str] = None,
    ) -> List[FileInfo]:
        """
        Upload multiple files to a channel.

        Args:
            channel_id: Channel ID to upload to
            files: List of (filename, file_data) tuples
            client_id: Client identifier

        Returns:
            List of uploaded file information
        """
        form_data = {
            "channel_id": channel_id,
        }
        if client_id:
            form_data["client_id"] = client_id

        # Prepare files for upload
        file_data = {}
        for i, (filename, content) in enumerate(files):
            file_data[f"files_{i}"] = (filename, content)

        headers = {"Content-Type": "multipart/form-data"}

        return await self._post(
            "files", List[FileInfo], data=file_data, headers=headers
        )

    async def get_file_info(self, file_id: str) -> FileInfo:
        """
        Get file information by ID.

        Args:
            file_id: File ID

        Returns:
            File information
        """
        return await self._get(f"files/{file_id}/info", FileInfo)

    async def get_file_metadata(self, file_id: str) -> FileInfo:
        """
        Get file metadata (alias for get_file_info).

        Args:
            file_id: File ID

        Returns:
            File metadata
        """
        return await self.get_file_info(file_id)

    async def get_file(self, file_id: str) -> bytes:
        """
        Download file content.

        Args:
            file_id: File ID

        Returns:
            File content as bytes
        """
        # Note: This returns raw file data, not a JSON model
        response = await self.client.get(f"files/{file_id}")
        return response

    async def get_file_thumbnail(self, file_id: str) -> bytes:
        """
        Get file thumbnail image.

        Args:
            file_id: File ID

        Returns:
            Thumbnail image as bytes
        """
        # Note: This returns raw image data, not a JSON model
        response = await self.client.get(f"files/{file_id}/thumbnail")
        return response

    async def get_file_preview(self, file_id: str) -> bytes:
        """
        Get file preview image.

        Args:
            file_id: File ID

        Returns:
            Preview image as bytes
        """
        # Note: This returns raw image data, not a JSON model
        response = await self.client.get(f"files/{file_id}/preview")
        return response

    async def get_file_link(self, file_id: str) -> Dict[str, str]:
        """
        Get a public link to a file.

        Args:
            file_id: File ID

        Returns:
            Dictionary containing the file link
        """
        response_data = await self.client.get(f"files/{file_id}/link")
        return response_data

    async def search_files(
        self,
        team_id: str,
        terms: str,
        is_or_search: bool = False,
        time_zone_offset: int = 0,
        include_deleted_channels: bool = False,
        page: int = 0,
        per_page: int = 60,
    ) -> Dict[str, Any]:
        """
        Search for files.

        Args:
            team_id: Team ID to search in
            terms: Search terms
            is_or_search: Whether to use OR logic between terms
            time_zone_offset: Timezone offset in seconds
            include_deleted_channels: Include files from deleted channels
            page: Page number (0-based)
            per_page: Files per page

        Returns:
            Search results
        """
        data = {
            "terms": terms,
            "is_or_search": is_or_search,
            "time_zone_offset": time_zone_offset,
            "include_deleted_channels": include_deleted_channels,
            "page": page,
            "per_page": per_page,
        }

        response_data = await self.client.post(
            f"teams/{team_id}/files/search", json=data
        )
        return response_data

    async def get_files_for_post(self, post_id: str) -> List[FileInfo]:
        """
        Get all files attached to a post.

        Args:
            post_id: Post ID

        Returns:
            List of file information
        """
        return await self._get_list(f"posts/{post_id}/files", FileInfo)

    async def delete_file(self, file_id: str) -> MattermostResponse:
        """
        Delete a file.

        Args:
            file_id: File ID to delete

        Returns:
            Response indicating success
        """
        return await self._delete(f"files/{file_id}", MattermostResponse)

    async def get_file_public_link(self, file_id: str) -> Dict[str, str]:
        """
        Generate a public link for a file.

        Args:
            file_id: File ID

        Returns:
            Dictionary containing the public link
        """
        return await self._post(f"files/{file_id}/link", Dict[str, str])

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get file extension from filename.

        Args:
            filename: Name of the file

        Returns:
            File extension (including the dot)
        """
        return os.path.splitext(filename)[1].lower()

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """
        Get MIME type from filename.

        Args:
            filename: Name of the file

        Returns:
            Estimated MIME type
        """
        import mimetypes

        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    @staticmethod
    def is_image_file(filename: str) -> bool:
        """
        Check if file is an image based on extension.

        Args:
            filename: Name of the file

        Returns:
            True if file appears to be an image
        """
        image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".svg",
            ".webp",
        }
        return FilesService.get_file_extension(filename) in image_extensions

    @staticmethod
    def is_video_file(filename: str) -> bool:
        """
        Check if file is a video based on extension.

        Args:
            filename: Name of the file

        Returns:
            True if file appears to be a video
        """
        video_extensions = {
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
        }
        return FilesService.get_file_extension(filename) in video_extensions

    @staticmethod
    def is_audio_file(filename: str) -> bool:
        """
        Check if file is an audio file based on extension.

        Args:
            filename: Name of the file

        Returns:
            True if file appears to be an audio file
        """
        audio_extensions = {
            ".mp3",
            ".wav",
            ".ogg",
            ".flac",
            ".aac",
            ".m4a",
            ".wma",
        }
        return FilesService.get_file_extension(filename) in audio_extensions

    async def get_file_stats(self) -> Dict[str, Any]:
        """
        Get file upload statistics.

        Returns:
            File statistics
        """
        response_data = await self.client.get("files/stats")
        return response_data
