# coding: utf-8
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import os
import json
import time

try:
    import xbmcvfs
    import xbmcaddon
except ImportError:
    # For testing outside Kodi environment
    xbmcvfs = None
    xbmcaddon = None


class SearchHistory:
    """Manages persistent storage and retrieval of search queries"""
    
    def __init__(self):
        """Initialize with path to Kodi addon data directory"""
        if xbmcaddon is not None:
            addon = xbmcaddon.Addon()
            data_path = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
        else:
            # Fallback for testing
            data_path = os.path.expanduser('~/.kodi/userdata/addon_data/plugin.video.jupiter.err.ee/')
        
        self.history_file = os.path.join(data_path, 'search_history.json')
        self.history = []
        self._load_history()
    
    def _load_history(self):
        """Load history from JSON file (private method)"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'entries' in data:
                        self.history = data['entries']
                    else:
                        self.history = []
            else:
                self.history = []
        except (IOError, OSError, json.JSONDecodeError) as e:
            # Log error and start with empty history
            print("Error loading search history: {}".format(str(e)))
            self.history = []
            # If file is corrupted, delete it
            if os.path.exists(self.history_file):
                try:
                    os.remove(self.history_file)
                except (IOError, OSError):
                    pass
    
    def _save_history(self):
        """Save history to JSON file (private method)"""
        try:
            # Ensure directory exists
            directory = os.path.dirname(self.history_file)
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            # Save with version for future compatibility
            data = {
                'version': 1,
                'entries': self.history
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError) as e:
            # Log error but don't crash
            print("Error saving search history: {}".format(str(e)))
    
    def get_history(self):
        """
        Retrieve all history entries
        
        Returns:
            list: List of dicts with 'query' and 'timestamp' keys,
                  ordered by most recent first
        """
        # Sort by timestamp descending (most recent first)
        sorted_history = sorted(self.history, key=lambda x: x.get('timestamp', 0), reverse=True)
        # Return only query and timestamp, not query_lower
        return [{'query': entry['query'], 'timestamp': entry['timestamp']} 
                for entry in sorted_history]
    
    def add_entry(self, query):
        """
        Add a search query to history
        - Handles duplicates by moving to top
        - Updates timestamp
        - Enforces 20 entry limit
        - Saves to disk
        
        Args:
            query (str): Search query text
        """
        # Validate input
        if not query or not query.strip():
            return
        
        query = query.strip()
        
        # Truncate if too long
        if len(query) > 500:
            query = query[:500]
        
        query_lower = query.lower()
        current_time = int(time.time())
        
        # Check for duplicates (case-insensitive)
        existing_index = None
        for i, entry in enumerate(self.history):
            if entry.get('query_lower', entry['query'].lower()) == query_lower:
                existing_index = i
                break
        
        if existing_index is not None:
            # Remove existing entry (will be re-added at top)
            self.history.pop(existing_index)
        
        # Add new entry at the beginning
        new_entry = {
            'query': query,
            'timestamp': current_time,
            'query_lower': query_lower
        }
        self.history.insert(0, new_entry)
        
        # Enforce 20 entry limit
        if len(self.history) > 20:
            self.history = self.history[:20]
        
        self._save_history()
    
    def remove_entry(self, query):
        """
        Remove a specific history entry
        
        Args:
            query (str): Search query to remove
        """
        query_lower = query.lower()
        
        # Find and remove the entry
        for i, entry in enumerate(self.history):
            if entry.get('query_lower', entry['query'].lower()) == query_lower:
                self.history.pop(i)
                self._save_history()
                break
    
    def clear(self):
        """Remove all history entries and delete storage file"""
        self.history = []
        
        # Delete the file
        if os.path.exists(self.history_file):
            try:
                os.remove(self.history_file)
            except (IOError, OSError) as e:
                print("Error deleting search history file: {}".format(str(e)))
