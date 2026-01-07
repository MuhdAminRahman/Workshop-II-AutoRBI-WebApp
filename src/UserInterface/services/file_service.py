import os
import shutil
from typing import List, Optional
from tkinter import filedialog, messagebox

class FileService:
    """Handles all file-related operations"""
    
    def __init__(self, pdf_converter, log_callback: Optional[callable] = None):
        self.pdf_converter = pdf_converter
        self.log_callback = log_callback or print
    
    def select_files(self, mode: str = "single") -> List[str]:
        """Open file dialog and return selected PDF files"""
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        
        try:
            if mode == "single":
                path = filedialog.askopenfilename(filetypes=filetypes)
                return [path] if path else []
            
            elif mode == "multiple":
                paths = filedialog.askopenfilenames(filetypes=filetypes)
                return list(paths) if paths else []
            
            elif mode == "folder":
                folder = filedialog.askdirectory(title="Select folder containing PDF files")
                if folder:
                    return self.find_pdfs_in_folder(folder)
                return []
        
        except Exception as e:
            self.log_callback(f"❌ File selection error: {e}")
            return []
    
    def find_pdfs_in_folder(self, folder_path: str) -> List[str]:
        """Find all PDF files in a folder recursively"""
        pdf_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files
    
    def convert_pdfs_to_images(self, pdf_paths: List[str], converted_img_dir: str) -> List[str]:
        """Convert PDF files to images and return equipment numbers"""
        all_converted = []
        
        # Ensure the output directory exists
        os.makedirs(converted_img_dir, exist_ok=True)
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                self.log_callback(f"⚠️ PDF not found: {os.path.basename(pdf_path)}")
                continue
            
            filename = os.path.basename(pdf_path)
            pdf_name_without_ext = os.path.splitext(filename)[0]
            
            # Get existing images for this PDF
            existing_images = self._get_existing_converted_images(pdf_name_without_ext, converted_img_dir)
            
            if existing_images:
                # Use existing converted images
                self._process_existing_images(existing_images, filename, all_converted)
                continue
            
            # Convert PDF to images
            self._convert_pdf_to_images(pdf_path, pdf_name_without_ext, converted_img_dir, filename, all_converted)
        
        return all_converted

    def _get_existing_converted_images(self, pdf_name: str, output_dir: str) -> List[str]:
        """Get existing converted images for a PDF"""
        existing_images = []
        if os.path.exists(output_dir):
            for f in os.listdir(output_dir):
                if (f.startswith(pdf_name) and 
                    f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))):
                    existing_images.append(os.path.join(output_dir, f))
        return existing_images

    def _process_existing_images(self, image_paths: List[str], filename: str, all_converted: List[str]):
        """Process already converted images"""
        self.log_callback(f"📄 PDF already converted: {filename}")
        self.log_callback(f"  📁 Found {len(image_paths)} existing image(s)")
        
        from data_extractor.utils import get_equipment_number_from_image_path
        for img_path in image_paths:
            equip_no = get_equipment_number_from_image_path(img_path)
            self.log_callback(f"    - Equipment No.: {equip_no}")
            all_converted.append(equip_no)

    def _convert_pdf_to_images(self, pdf_path: str, pdf_name: str, output_dir: str, 
                            filename: str, all_converted: List[str]):
        """Convert a PDF to images and process them"""
        self.log_callback(f"📄 Converting PDF: {filename}")
        
        try:
            # Convert PDF
            image_paths = self.pdf_converter.convert_single(pdf_path, output_folder=output_dir)
            
            # If converter doesn't support output_dir, rename/move files
            if image_paths and os.path.dirname(image_paths[0]) != output_dir:
                renamed_paths = []
                for i, img_path in enumerate(image_paths):
                    new_name = f"{pdf_name}_page_{i+1}{os.path.splitext(img_path)[1]}"
                    new_path = os.path.join(output_dir, new_name)
                    shutil.move(img_path, new_path)
                    renamed_paths.append(new_path)
                image_paths = renamed_paths
            
            if image_paths:
                from data_extractor.utils import get_equipment_number_from_image_path
                for img_path in image_paths:
                    equip_no = get_equipment_number_from_image_path(img_path)
                    self.log_callback(f"    - Equipment No.: {equip_no}")
                    all_converted.append(equip_no)
                
                self.log_callback(f"  ✅ Created {len(image_paths)} image(s)")
            else:
                self.log_callback(f"  ❌ Failed to convert {filename}")
        
        except Exception as e:
            self.log_callback(f"  ❌ Error: {str(e)}")
    
    def get_work_excel_path(self, work_id: str, project_root: str) -> Optional[str]:
        """Get path to Excel file for a work"""
        try:
            excel_dir = os.path.join(project_root, "src", "output_files", work_id, "excel", "updated")
            default_dir = os.path.join(project_root, "src", "output_files", work_id, "excel", "default")

            # First check the updated directory
            if os.path.isdir(excel_dir):
                for fname in os.listdir(excel_dir):
                    if fname.lower().endswith(('.xlsx', '.xls')):
                        return os.path.join(excel_dir, fname)

            # If no Excel files found in updated, check default directory
            if os.path.isdir(default_dir):
                for fname in os.listdir(default_dir):
                    if fname.lower().endswith(('.xlsx', '.xls')):
                        return os.path.join(default_dir, fname)
            
        except Exception:
            pass
        return None