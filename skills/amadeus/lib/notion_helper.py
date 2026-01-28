"""
Notion API helper for creating travel proposal pages.

Manages Notion integration for storing and organizing travel research.
"""

import os
import requests
from typing import Optional, Dict, List, Any


class NotionError(Exception):
    """Raised when Notion API call fails."""
    pass


class NotionHelper:
    """
    Helper for interacting with Notion API.
    
    Requires NOTION_API_KEY environment variable.
    """
    
    NOTION_VERSION = "2025-09-03"
    BASE_URL = "https://api.notion.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Notion helper.
        
        Args:
            api_key: Notion API key (falls back to NOTION_API_KEY env var)
            
        Raises:
            NotionError: If API key not found
        """
        self.api_key = api_key or os.environ.get('NOTION_API_KEY')
        if not self.api_key:
            raise NotionError(
                "Notion API key not configured. "
                "Set NOTION_API_KEY environment variable."
            )
    
    def _headers(self) -> Dict[str, str]:
        """Get headers for Notion API requests."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Notion-Version': self.NOTION_VERSION,
            'Content-Type': 'application/json',
        }
    
    def search(self, query: str, object_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for pages and databases by title.
        
        Args:
            query: Search query
            object_type: Filter by type ('page' or 'database')
            
        Returns:
            List of matching pages/databases
        """
        payload = {'query': query}
        if object_type:
            payload['filter'] = {'object': object_type}
        
        try:
            response = requests.post(
                f'{self.BASE_URL}/search',
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.RequestException as e:
            raise NotionError(f'Search failed: {e}')
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page details."""
        try:
            response = requests.get(
                f'{self.BASE_URL}/pages/{page_id}',
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NotionError(f'Failed to get page: {e}')
    
    def create_page(
        self,
        parent_id: str,
        title: str,
        properties: Optional[Dict[str, Any]] = None,
        is_database_parent: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new page.
        
        Args:
            parent_id: ID of parent page or database
            title: Page title
            properties: Additional page properties
            is_database_parent: If True, parent is a database (data source)
        """
        parent_key = 'database_id' if is_database_parent else 'page_id'
        
        payload = {
            'parent': {parent_key: parent_id},
            'properties': {
                'title': [{'text': {'content': title}}],
                **(properties or {}),
            },
        }
        
        try:
            response = requests.post(
                f'{self.BASE_URL}/pages',
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NotionError(f'Failed to create page: {e}')
    
    def append_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Append blocks (content) to a page.
        
        Args:
            page_id: Page ID
            blocks: List of block objects to append
        """
        payload = {'children': blocks}
        
        try:
            response = requests.patch(
                f'{self.BASE_URL}/blocks/{page_id}/children',
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise NotionError(f'Failed to append blocks: {e}')
    
    @staticmethod
    def heading_block(text: str, level: int = 1) -> Dict[str, Any]:
        """Create a heading block."""
        heading_type = f'heading_{level}'
        return {
            'object': 'block',
            'type': heading_type,
            heading_type: {
                'rich_text': [{'text': {'content': text}}],
            },
        }
    
    @staticmethod
    def paragraph_block(text: str, bold: bool = False, code: bool = False) -> Dict[str, Any]:
        """Create a paragraph block."""
        return {
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{
                    'text': {
                        'content': text,
                    },
                    'annotations': {
                        'bold': bold,
                        'code': code,
                    },
                }],
            },
        }
    
    @staticmethod
    def divider_block() -> Dict[str, Any]:
        """Create a divider block."""
        return {
            'object': 'block',
            'type': 'divider',
            'divider': {},
        }
    
    @staticmethod
    def code_block(code: str, language: str = 'json') -> Dict[str, Any]:
        """Create a code block."""
        return {
            'object': 'block',
            'type': 'code',
            'code': {
                'rich_text': [{'text': {'content': code}}],
                'language': language,
            },
        }
    
    @staticmethod
    def table_block(
        headers: List[str],
        rows: List[List[str]],
        has_column_header: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a table block.
        
        Args:
            headers: List of column headers
            rows: List of rows (each row is list of cell values)
            has_column_header: Whether first row is headers
        """
        return {
            'object': 'block',
            'type': 'table',
            'table': {
                'table_width': len(headers),
                'has_column_header': has_column_header,
                'children': [
                    {
                        'object': 'block',
                        'type': 'table_row',
                        'table_row': {
                            'cells': [[{'text': {'content': str(cell)}}] for cell in row],
                        },
                    }
                    for row in [headers] + rows
                ],
            },
        }
    
    @staticmethod
    def bulleted_list_block(items: List[str]) -> List[Dict[str, Any]]:
        """Create bulleted list blocks."""
        return [
            {
                'object': 'block',
                'type': 'bulleted_list_item',
                'bulleted_list_item': {
                    'rich_text': [{'text': {'content': item}}],
                },
            }
            for item in items
        ]
