"""
BrowserUse Agent Helper - CDP + Playwright + BrowserUse 集成

提供统一的浏览器管理和自定义工具支持
"""

from .browser_manager import SimpleBrowserManager, get_or_create_browser
from .tools import tools, set_browser_manager

__all__ = [
    'SimpleBrowserManager',
    'get_or_create_browser',
    'tools',
    'set_browser_manager',
]

__version__ = '0.1.0'
