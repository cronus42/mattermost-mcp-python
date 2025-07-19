"""
Posts service for Mattermost API operations.

This module provides high-level async methods for post-related operations
mapped to REST endpoints, returning typed models.
"""

from typing import List, Optional, Dict, Any

from .base import BaseService
from ..models.posts import (
    Post,
    PostCreate,
    PostPatch,
    PostList,
    PostListWithSearchMatches,
    PostSearch,
    PostAction,
    Reaction,
    FileInfo,
)
from ..models.base import MattermostResponse


class PostsService(BaseService):
    """
    Service for post-related operations.
    
    Provides high-level async methods for:
    - Creating, updating, and deleting posts
    - Getting post information and lists
    - Post search functionality
    - Reactions and file attachments
    """
    
    async def create_post(self, post_data: PostCreate) -> Post:
        """
        Create a new post.
        
        Args:
            post_data: Post creation data
            
        Returns:
            Created post
        """
        return await self._post(
            "posts",
            Post,
            data=post_data.model_dump(exclude_none=True)
        )
    
    async def get_post(self, post_id: str) -> Post:
        """
        Get a post by ID.
        
        Args:
            post_id: Post ID
            
        Returns:
            Post information
        """
        return await self._get(f"posts/{post_id}", Post)
    
    async def update_post(self, post_id: str, post_patch: PostPatch) -> Post:
        """
        Update a post's information.
        
        Args:
            post_id: Post ID
            post_patch: Post update data
            
        Returns:
            Updated post
        """
        return await self._put(
            f"posts/{post_id}",
            Post,
            data=post_patch.model_dump(exclude_none=True)
        )
    
    async def patch_post(self, post_id: str, post_patch: PostPatch) -> Post:
        """
        Partially update a post's information.
        
        Args:
            post_id: Post ID
            post_patch: Post patch data
            
        Returns:
            Updated post
        """
        return await self._patch(
            f"posts/{post_id}/patch",
            Post,
            data=post_patch.model_dump(exclude_none=True)
        )
    
    async def delete_post(self, post_id: str) -> MattermostResponse:
        """
        Delete a post.
        
        Args:
            post_id: Post ID
            
        Returns:
            Response indicating success
        """
        return await self._delete(f"posts/{post_id}", MattermostResponse)
    
    async def get_posts_for_channel(
        self,
        channel_id: str,
        page: int = 0,
        per_page: int = 60,
        since: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> PostList:
        """
        Get posts for a channel.
        
        Args:
            channel_id: Channel ID
            page: Page number (0-based)
            per_page: Number of posts per page
            since: Get posts since timestamp
            before: Get posts before this post ID
            after: Get posts after this post ID
            
        Returns:
            List of posts with order information
        """
        params = self._build_query_params(
            page=page,
            per_page=per_page,
            since=since,
            before=before,
            after=after,
        )
        
        return await self._get(f"channels/{channel_id}/posts", PostList, params=params)
    
    async def get_posts_around(
        self,
        channel_id: str,
        post_id: str,
        before: int = 10,
        after: int = 10,
    ) -> PostList:
        """
        Get posts around a specific post.
        
        Args:
            channel_id: Channel ID
            post_id: Center post ID
            before: Number of posts before
            after: Number of posts after
            
        Returns:
            List of posts around the specified post
        """
        params = self._build_query_params(before=before, after=after)
        return await self._get(
            f"channels/{channel_id}/posts/{post_id}/context",
            PostList,
            params=params
        )
    
    async def get_posts_since(self, channel_id: str, since: int) -> PostList:
        """
        Get posts since a timestamp.
        
        Args:
            channel_id: Channel ID
            since: Timestamp to get posts since
            
        Returns:
            List of posts since the timestamp
        """
        params = {"since": since}
        return await self._get(f"channels/{channel_id}/posts", PostList, params=params)
    
    async def search_posts(
        self,
        team_id: str,
        search_data: PostSearch,
    ) -> PostListWithSearchMatches:
        """
        Search for posts.
        
        Args:
            team_id: Team ID to search in
            search_data: Search criteria
            
        Returns:
            Search results with match information
        """
        return await self._post(
            f"teams/{team_id}/posts/search",
            PostListWithSearchMatches,
            data=search_data.model_dump(exclude_none=True)
        )
    
    async def pin_post(self, post_id: str) -> MattermostResponse:
        """
        Pin a post to its channel.
        
        Args:
            post_id: Post ID to pin
            
        Returns:
            Response indicating success
        """
        return await self._post(f"posts/{post_id}/pin", MattermostResponse)
    
    async def unpin_post(self, post_id: str) -> MattermostResponse:
        """
        Unpin a post from its channel.
        
        Args:
            post_id: Post ID to unpin
            
        Returns:
            Response indicating success
        """
        return await self._delete(f"posts/{post_id}/pin", MattermostResponse)
    
    async def get_post_thread(self, post_id: str) -> PostList:
        """
        Get a post's thread (replies).
        
        Args:
            post_id: Root post ID
            
        Returns:
            Post thread with all replies
        """
        return await self._get(f"posts/{post_id}/thread", PostList)
    
    async def get_flagged_posts(
        self,
        user_id: str,
        team_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        page: int = 0,
        per_page: int = 60,
    ) -> PostList:
        """
        Get flagged posts for a user.
        
        Args:
            user_id: User ID
            team_id: Filter by team ID
            channel_id: Filter by channel ID
            page: Page number (0-based)
            per_page: Number of posts per page
            
        Returns:
            List of flagged posts
        """
        params = self._build_query_params(
            team_id=team_id,
            channel_id=channel_id,
            page=page,
            per_page=per_page,
        )
        
        return await self._get(f"users/{user_id}/posts/flagged", PostList, params=params)
    
    # Reaction Methods
    
    async def add_reaction(self, user_id: str, post_id: str, emoji_name: str) -> Reaction:
        """
        Add a reaction to a post.
        
        Args:
            user_id: User ID adding the reaction
            post_id: Post ID
            emoji_name: Emoji name
            
        Returns:
            Created reaction
        """
        data = {
            "user_id": user_id,
            "post_id": post_id,
            "emoji_name": emoji_name,
        }
        return await self._post("reactions", Reaction, data=data)
    
    async def remove_reaction(self, user_id: str, post_id: str, emoji_name: str) -> MattermostResponse:
        """
        Remove a reaction from a post.
        
        Args:
            user_id: User ID removing the reaction
            post_id: Post ID
            emoji_name: Emoji name
            
        Returns:
            Response indicating success
        """
        return await self._delete(f"users/{user_id}/posts/{post_id}/reactions/{emoji_name}", MattermostResponse)
    
    async def get_reactions(self, post_id: str) -> List[Reaction]:
        """
        Get all reactions for a post.
        
        Args:
            post_id: Post ID
            
        Returns:
            List of reactions
        """
        return await self._get_list(f"posts/{post_id}/reactions", Reaction)
    
    # File Methods (related to posts)
    
    async def get_file_info(self, file_id: str) -> FileInfo:
        """
        Get file information.
        
        Args:
            file_id: File ID
            
        Returns:
            File information
        """
        return await self._get(f"files/{file_id}/info", FileInfo)
    
    async def get_file(self, file_id: str) -> bytes:
        """
        Get file content.
        
        Args:
            file_id: File ID
            
        Returns:
            File content as bytes
        """
        # Note: This returns raw file data, not a model
        response = await self.client.get(f"files/{file_id}")
        return response
    
    async def get_file_thumbnail(self, file_id: str) -> bytes:
        """
        Get file thumbnail.
        
        Args:
            file_id: File ID
            
        Returns:
            Thumbnail content as bytes
        """
        # Note: This returns raw image data, not a model
        response = await self.client.get(f"files/{file_id}/thumbnail")
        return response
    
    async def get_file_preview(self, file_id: str) -> bytes:
        """
        Get file preview.
        
        Args:
            file_id: File ID
            
        Returns:
            Preview content as bytes
        """
        # Note: This returns raw image data, not a model
        response = await self.client.get(f"files/{file_id}/preview")
        return response
