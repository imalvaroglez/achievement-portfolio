# Amadeus API Library
try:
    from .auth import AmadeusAuth
    from .client import AmadeusClient
    from .cache import ResponseCache
    from .notion_helper import NotionHelper
except ImportError:
    from auth import AmadeusAuth
    from client import AmadeusClient
    from cache import ResponseCache
    try:
        from notion_helper import NotionHelper
    except ImportError:
        NotionHelper = None

__all__ = ['AmadeusAuth', 'AmadeusClient', 'ResponseCache', 'NotionHelper']
