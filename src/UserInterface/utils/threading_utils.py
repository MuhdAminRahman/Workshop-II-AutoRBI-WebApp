import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Optional, Any
from contextlib import contextmanager

class SafeThreadExecutor:
    """Thread executor with safe cleanup"""
    
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._shutdown = False
    
    def submit(self, fn: Callable, *args, **kwargs) -> Optional[Future]:
        """Submit task to executor"""
        if self._shutdown:
            return None
        
        try:
            return self.executor.submit(fn, *args, **kwargs)
        except Exception as e:
            print(f"Error submitting task: {e}")
            return None
    
    def shutdown(self, wait: bool = False) -> None:
        """Shutdown executor"""
        self._shutdown = True
        self.executor.shutdown(wait=wait)
    
    def __del__(self):
        """Cleanup on destruction"""
        self.shutdown(wait=False)


class LoadingContext:
    """Context manager for loading states"""
    
    def __init__(self, controller, message: str, show_progress: bool = False):
        self.controller = controller
        self.message = message
        self.show_progress = show_progress
    
    def __enter__(self):
        """Show loading indicator"""
        if hasattr(self.controller, 'show_loading'):
            try:
                self.controller.show_loading(self.message, show_progress=self.show_progress)
            except Exception as e:
                print(f"Could not show loading: {e}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Hide loading indicator"""
        if hasattr(self.controller, 'hide_loading'):
            try:
                self.controller.hide_loading()
            except Exception as e:
                print(f"Could not hide loading: {e}")
        return False  # Don't suppress exceptions
    
    def update_progress(self, progress: float, message: str):
        """Update progress during loading"""
        if hasattr(self.controller, 'update_loading_progress'):
            try:
                self.controller.update_loading_progress(progress, message)
            except Exception as e:
                print(f"Could not update progress: {e}")
