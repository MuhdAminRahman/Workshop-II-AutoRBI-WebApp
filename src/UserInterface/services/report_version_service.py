"""
Report Version Service - Manages versioning of Excel and PowerPoint files.

This service handles:
- Tracking different versions of reports (original extraction vs edited versions)
- Managing file storage in proper directories
- Version metadata and history
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ReportVersion:
    """Represents a single version of a report."""
    version_number: int
    version_type: str  # 'extraction' or 'edited'
    created_at: str
    created_by: Optional[int]  # User ID
    excel_path: Optional[str]
    ppt_path: Optional[str]
    notes: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ReportVersionService:
    """Service for managing report versions."""
    
    VERSION_METADATA_FILE = "version_metadata.json"
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.output_dir = os.path.join(project_root, "src", "output_files")
    
    def get_work_directory(self, work_name: str) -> str:
        """Get the output directory for a specific work."""
        return os.path.join(self.output_dir, work_name)
    
    def get_version_metadata_path(self, work_name: str) -> str:
        """Get path to version metadata file."""
        work_dir = self.get_work_directory(work_name)
        return os.path.join(work_dir, self.VERSION_METADATA_FILE)
    
    def load_version_metadata(self, work_name: str) -> List[ReportVersion]:
        """Load version metadata from JSON file."""
        metadata_path = self.get_version_metadata_path(work_name)
        
        if not os.path.exists(metadata_path):
            return []
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            
            versions = []
            for item in data:
                versions.append(ReportVersion(**item))
            
            return versions
            
        except Exception as e:
            print(f"Error loading version metadata: {e}")
            return []
    
    def save_version_metadata(self, work_name: str, versions: List[ReportVersion]) -> bool:
        """Save version metadata to JSON file."""
        metadata_path = self.get_version_metadata_path(work_name)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            
            # Convert to dict and save
            data = [v.to_dict() for v in versions]
            
            with open(metadata_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving version metadata: {e}")
            return False
    
    def register_extraction_version(
        self,
        work_name: str,
        user_id: int,
        excel_path: str,
        ppt_path: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ReportVersion:
        """
        Register the initial extraction version.
        
        This is called after the first extraction from PDFs.
        """
        versions = self.load_version_metadata(work_name)
        
        # Create new version
        new_version = ReportVersion(
            version_number=1,
            version_type='extraction',
            created_at=datetime.now().isoformat(),
            created_by=user_id,
            excel_path=excel_path,
            ppt_path=ppt_path,
            notes=notes or "Initial extraction from GA drawings"
        )
        
        versions.append(new_version)
        self.save_version_metadata(work_name, versions)
        
        return new_version
    
    def register_edited_version(
        self,
        work_name: str,
        user_id: int,
        excel_path: str,
        ppt_path: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ReportVersion:
        """
        Register a new edited version.
        
        This is called after user edits and regenerates.
        """
        versions = self.load_version_metadata(work_name)
        
        # Get next version number
        next_version = len(versions) + 1
        
        # Create new version
        new_version = ReportVersion(
            version_number=next_version,
            version_type='edited',
            created_at=datetime.now().isoformat(),
            created_by=user_id,
            excel_path=excel_path,
            ppt_path=ppt_path,
            notes=notes or f"Manual edit #{next_version - 1}"
        )
        
        versions.append(new_version)
        self.save_version_metadata(work_name, versions)
        
        return new_version
    
    def get_latest_version(self, work_name: str) -> Optional[ReportVersion]:
        """Get the most recent version."""
        versions = self.load_version_metadata(work_name)
        
        if not versions:
            return None
        
        return versions[-1]
    
    def get_version_by_number(self, work_name: str, version_number: int) -> Optional[ReportVersion]:
        """Get a specific version by number."""
        versions = self.load_version_metadata(work_name)
        
        for version in versions:
            if version.version_number == version_number:
                return version
        
        return None
    
    def get_all_versions(self, work_name: str) -> List[ReportVersion]:
        """Get all versions for a work."""
        return self.load_version_metadata(work_name)
    
    def delete_version(self, work_name: str, version_number: int) -> bool:
        """
        Delete a specific version and its files.
        
        Note: Cannot delete version 1 (original extraction).
        """
        if version_number == 1:
            print("Cannot delete original extraction version")
            return False
        
        versions = self.load_version_metadata(work_name)
        
        # Find and remove version
        version_to_delete = None
        for i, version in enumerate(versions):
            if version.version_number == version_number:
                version_to_delete = version
                versions.pop(i)
                break
        
        if not version_to_delete:
            return False
        
        # Delete files
        try:
            if version_to_delete.excel_path and os.path.exists(version_to_delete.excel_path):
                os.remove(version_to_delete.excel_path)
            
            if version_to_delete.ppt_path and os.path.exists(version_to_delete.ppt_path):
                os.remove(version_to_delete.ppt_path)
            
            # Save updated metadata
            self.save_version_metadata(work_name, versions)
            
            return True
            
        except Exception as e:
            print(f"Error deleting version files: {e}")
            return False
    
    def get_version_comparison(
        self,
        work_name: str,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """
        Compare two versions (for future enhancement).
        
        Returns metadata about differences between versions.
        """
        v1 = self.get_version_by_number(work_name, version1)
        v2 = self.get_version_by_number(work_name, version2)
        
        if not v1 or not v2:
            return {}
        
        return {
            'version1': v1.to_dict(),
            'version2': v2.to_dict(),
            'time_difference': self._calculate_time_diff(v1.created_at, v2.created_at),
            # Add more comparison logic as needed
        }
    
    def _calculate_time_diff(self, time1: str, time2: str) -> str:
        """Calculate human-readable time difference."""
        try:
            dt1 = datetime.fromisoformat(time1)
            dt2 = datetime.fromisoformat(time2)
            
            diff = abs((dt2 - dt1).total_seconds())
            
            if diff < 60:
                return f"{int(diff)} seconds"
            elif diff < 3600:
                return f"{int(diff / 60)} minutes"
            elif diff < 86400:
                return f"{int(diff / 3600)} hours"
            else:
                return f"{int(diff / 86400)} days"
                
        except Exception:
            return "Unknown"
    
    def cleanup_old_versions(
        self,
        work_name: str,
        keep_recent: int = 5
    ) -> Tuple[int, List[str]]:
        """
        Clean up old versions, keeping only the most recent ones.
        
        Args:
            work_name: Name of the work
            keep_recent: Number of recent versions to keep
        
        Returns:
            Tuple of (number_deleted, list_of_errors)
        """
        versions = self.load_version_metadata(work_name)
        
        if len(versions) <= keep_recent:
            return 0, []
        
        # Always keep version 1 (original extraction)
        versions_to_keep = [versions[0]]  # Version 1
        
        # Keep the most recent versions
        recent_versions = sorted(
            versions[1:],
            key=lambda v: v.created_at,
            reverse=True
        )[:keep_recent - 1]
        
        versions_to_keep.extend(recent_versions)
        
        # Delete the rest
        versions_to_delete = [v for v in versions if v not in versions_to_keep]
        
        deleted_count = 0
        errors = []
        
        for version in versions_to_delete:
            try:
                if version.excel_path and os.path.exists(version.excel_path):
                    os.remove(version.excel_path)
                
                if version.ppt_path and os.path.exists(version.ppt_path):
                    os.remove(version.ppt_path)
                
                deleted_count += 1
                
            except Exception as e:
                errors.append(f"Version {version.version_number}: {str(e)}")
        
        # Save updated metadata
        self.save_version_metadata(work_name, versions_to_keep)
        
        return deleted_count, errors
    
    def export_version_history(self, work_name: str) -> str:
        """
        Export version history as a readable text file.
        
        Returns path to exported file.
        """
        versions = self.load_version_metadata(work_name)
        
        if not versions:
            return ""
        
        work_dir = self.get_work_directory(work_name)
        export_path = os.path.join(work_dir, f"{work_name}_version_history.txt")
        
        try:
            with open(export_path, 'w') as f:
                f.write(f"Version History for: {work_name}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n\n")
                
                for version in versions:
                    f.write(f"Version {version.version_number} ({version.version_type})\n")
                    f.write(f"  Created: {version.created_at}\n")
                    f.write(f"  Created by: User ID {version.created_by}\n")
                    
                    if version.excel_path:
                        f.write(f"  Excel: {os.path.basename(version.excel_path)}\n")
                    
                    if version.ppt_path:
                        f.write(f"  PowerPoint: {os.path.basename(version.ppt_path)}\n")
                    
                    if version.notes:
                        f.write(f"  Notes: {version.notes}\n")
                    
                    f.write("\n")
            
            return export_path
            
        except Exception as e:
            print(f"Error exporting version history: {e}")
            return ""
    
    def get_version_statistics(self, work_name: str) -> Dict[str, Any]:
        """Get statistics about versions."""
        versions = self.load_version_metadata(work_name)
        
        if not versions:
            return {
                'total_versions': 0,
                'extraction_versions': 0,
                'edited_versions': 0,
                'first_created': None,
                'last_modified': None,
                'total_edits': 0
            }
        
        edited_versions = [v for v in versions if v.version_type == 'edited']
        
        return {
            'total_versions': len(versions),
            'extraction_versions': len([v for v in versions if v.version_type == 'extraction']),
            'edited_versions': len(edited_versions),
            'first_created': versions[0].created_at if versions else None,
            'last_modified': versions[-1].created_at if versions else None,
            'total_edits': len(edited_versions)
        }