from queue import Queue, Empty
from typing import Callable, Any, Dict, Optional
import customtkinter as ctk

class UIUpdateManager:
    """Manages batched UI updates from background threads"""
    
    def __init__(self, parent: ctk.CTk, batch_interval_ms: int = 100):
        self.parent = parent
        self.batch_interval = batch_interval_ms
        self.update_queue = Queue()
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        
    def start(self):
        """Start processing UI updates"""
        if not self._running:
            self._running = True
            self._process_updates()
    
    def stop(self):
        """Stop processing UI updates"""
        self._running = False
    
    def register_handler(self, update_type: str, handler: Callable):
        """Register a handler for an update type"""
        self._handlers[update_type] = handler
    
    def queue_update(self, update_type: str, data: Any = None):
        """Queue an update from any thread"""
        self.update_queue.put((update_type, data))
    
    def _process_updates(self):
        """Process pending UI updates in batches"""
        if not self._running:
            return
        
        updates_processed = 0
        max_updates_per_batch = 50
        
        try:
            # Process multiple updates in one batch
            while updates_processed < max_updates_per_batch:
                try:
                    update_type, data = self.update_queue.get_nowait()
                    
                    # Call registered handler
                    handler = self._handlers.get(update_type)
                    if handler:
                        handler(data)
                    
                    updates_processed += 1
                    
                except Empty:
                    break
                except Exception as e:
                    print(f"Error processing update: {e}")
        
        except Exception as e:
            print(f"Error in update batch: {e}")
        
        # Schedule next batch
        if self._running:
            self.parent.after(self.batch_interval, self._process_updates)