import os
from pdf2image import convert_from_path

class PDFToImageConverter:
    """
    A class to convert PDF files to images, supporting both single and batch conversion
    """
    
    def __init__(self, output_folder="converted_to_image", dpi=200, use_page_numbers=True):
        """
        Initialize the PDF to Image Converter
        
        Args:
            output_folder: Default folder to save images
            dpi: Default resolution for conversion
            use_page_numbers: Whether to add page numbers for multi-page PDFs
        """
        self.output_folder = output_folder
        self.default_dpi = dpi
        self.use_page_numbers = use_page_numbers
        
        # Create output folder if it doesn't exist
        self._ensure_output_folder()
    
    def _ensure_output_folder(self, custom_folder=None):
        """
        Ensure the output folder exists
        
        Args:
            custom_folder: Optional custom folder path
        
        Returns:
            Path to the output folder
        """
        folder = custom_folder if custom_folder else self.output_folder
        os.makedirs(folder, exist_ok=True)
        return folder
    
    def convert_single(self, pdf_path, output_folder=None, dpi=None, use_page_numbers=None):
        """
        Convert a single PDF file to images
        
        Args:
            pdf_path: Path to the PDF file
            output_folder: Folder to save images (uses default if None)
            dpi: Resolution for conversion (uses default if None)
            use_page_numbers: Whether to add page numbers (uses default if None)
        
        Returns:
            List of paths to created image files
        """
        # Use instance defaults if parameters not provided
        output_folder = self._ensure_output_folder(output_folder)
        dpi = dpi if dpi is not None else self.default_dpi
        use_page_numbers = use_page_numbers if use_page_numbers is not None else self.use_page_numbers
        
        # Check if PDF file exists
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file '{pdf_path}' does not exist!")
            return []
        
        if not pdf_path.lower().endswith('.pdf'):
            print(f"Error: '{pdf_path}' is not a PDF file!")
            return []
        
        pdf_filename = os.path.basename(pdf_path)
        base_name = os.path.splitext(pdf_filename)[0]
        created_files = []
        
        try:
            print(f"\nConverting: {pdf_filename}")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=dpi)
            
            # Save each page
            for i, image in enumerate(images):
                if len(images) == 1 and not use_page_numbers:
                    # Single page - use exact PDF name
                    output_path = os.path.join(output_folder, f"{base_name}.png")
                else:
                    # Multiple pages or force page numbers
                    output_path = os.path.join(output_folder, f"{base_name}_page_{i+1:03d}.png")
                
                image.save(output_path, "PNG")
                created_files.append(output_path)
                print(f"  Saved: {os.path.basename(output_path)}")
            
            print(f"✓ Completed: {pdf_filename} → {len(images)} pages")
            return created_files
            
        except Exception as e:
            print(f"✗ Error converting {pdf_filename}: {e}")
            return []
    
    def convert_batch(self, input_folder, output_folder=None, dpi=None, use_page_numbers=None):
        """
        Convert all PDF files in a folder to images
        
        Args:
            input_folder: Folder containing PDF files
            output_folder: Folder to save images (uses default if None)
            dpi: Resolution for conversion (uses default if None)
            use_page_numbers: Whether to add page numbers (uses default if None)
        
        Returns:
            Dictionary with PDF names as keys and list of created image paths as values
        """
        # Use instance defaults if parameters not provided
        output_folder = self._ensure_output_folder(output_folder)
        dpi = dpi if dpi is not None else self.default_dpi
        use_page_numbers = use_page_numbers if use_page_numbers is not None else self.use_page_numbers
        
        # Check if input folder exists
        if not os.path.exists(input_folder):
            print(f"Error: Input folder '{input_folder}' does not exist!")
            return {}
        
        # Get all PDF files
        pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF files found in '{input_folder}'")
            return {}
        
        print(f"Found {len(pdf_files)} PDF files to convert:")
        for pdf_file in pdf_files:
            print(f"  - {pdf_file}")
        
        total_pages = 0
        results = {}
        
        # Convert each PDF file
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_folder, pdf_file)
            
            # Use the single file conversion method
            created_files = self.convert_single(
                pdf_path, 
                output_folder, 
                dpi, 
                use_page_numbers
            )
            
            if created_files:
                results[pdf_file] = created_files
                total_pages += len(created_files)
        
        print(f"\n🎉 Batch conversion complete!")
        print(f"📁 PDF files processed: {len(results)}")
        print(f"📄 Total pages converted: {total_pages}")
        print(f"💾 Images saved in: {os.path.abspath(output_folder)}/")
        
        return results
    
    def convert(self, input_path, output_folder=None, dpi=None, use_page_numbers=None):
        """
        Universal method that handles both single file and folder conversion
        
        Args:
            input_path: Either a PDF file path or a folder path
            output_folder: Folder to save images (uses default if None)
            dpi: Resolution for conversion (uses default if None)
            use_page_numbers: Whether to add page numbers (uses default if None)
        
        Returns:
            For single file: List of created image paths
            For folder: Dictionary with results
            None if invalid input
        """
        # Use instance defaults if parameters not provided
        output_folder = self._ensure_output_folder(output_folder)
        dpi = dpi if dpi is not None else self.default_dpi
        use_page_numbers = use_page_numbers if use_page_numbers is not None else self.use_page_numbers
        
        if os.path.isfile(input_path):
            print(f"📄 Processing single file: {os.path.basename(input_path)}")
            return self.convert_single(input_path, output_folder, dpi, use_page_numbers)
        
        elif os.path.isdir(input_path):
            print(f"📁 Processing folder: {input_path}")
            return self.convert_batch(input_path, output_folder, dpi, use_page_numbers)
        
        else:
            print(f"Error: '{input_path}' is neither a valid file nor folder!")
            return None
    
    def update_settings(self, output_folder=None, dpi=None, use_page_numbers=None):
        """
        Update the converter settings
        
        Args:
            output_folder: New default output folder
            dpi: New default DPI
            use_page_numbers: New default for page numbers
        """
        if output_folder is not None:
            self.output_folder = output_folder
            self._ensure_output_folder()
        
        if dpi is not None:
            self.default_dpi = dpi
        
        if use_page_numbers is not None:
            self.use_page_numbers = use_page_numbers
        
        print(f"Settings updated:")
        print(f"  Output folder: {self.output_folder}")
        print(f"  DPI: {self.default_dpi}")
        print(f"  Use page numbers: {self.use_page_numbers}")
    
    def get_settings(self):
        """
        Get current converter settings
        
        Returns:
            Dictionary with current settings
        """
        return {
            'output_folder': self.output_folder,
            'dpi': self.default_dpi,
            'use_page_numbers': self.use_page_numbers
        }
    
    def list_pdf_files(self, folder_path):
        """
        List all PDF files in a folder
        
        Args:
            folder_path: Path to the folder
        
        Returns:
            List of PDF filenames
        """
        if not os.path.exists(folder_path):
            print(f"Error: Folder '{folder_path}' does not exist!")
            return []
        
        if not os.path.isdir(folder_path):
            print(f"Error: '{folder_path}' is not a folder!")
            return []
        
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        
        if pdf_files:
            print(f"Found {len(pdf_files)} PDF files in '{folder_path}':")
            for i, pdf_file in enumerate(pdf_files, 1):
                print(f"  {i:2d}. {pdf_file}")
        else:
            print(f"No PDF files found in '{folder_path}'")
        
        return pdf_files

# Example usage
if __name__ == "__main__":
    # Create converter instance with default settings
    converter = PDFToImageConverter()
    
    print("=== PDF to Image Converter ===")
    print("Current settings:", converter.get_settings())
    
    # Option 1: Convert a single PDF file
    print("\n=== Option 1: Single File Conversion ===")
    single_file = "document.pdf"  # Replace with your PDF file
    if os.path.exists(single_file):
        converter.convert_single(single_file)
    
    # Option 2: Convert multiple PDFs from a folder
    print("\n=== Option 2: Folder Conversion ===")
    input_folder = "CaseStudy1Resources"
    if os.path.exists(input_folder):
        converter.convert_batch(input_folder)
    
    # Option 3: Use the universal convert method
    print("\n=== Option 3: Universal Conversion Method ===")
    
    # For single file
    # converter.convert("document.pdf")
    
    # For folder
    # converter.convert("CaseStudy1Resources")
    
    # Option 4: Change settings and convert
    print("\n=== Option 4: Custom Settings ===")
    converter.update_settings(dpi=300, use_page_numbers=False)
    print("Updated settings:", converter.get_settings())
    
    # Now convert with new settings
    if os.path.exists(single_file):
        converter.convert_single(single_file)
    
    # Reset to defaults
    converter.update_settings(output_folder="converted_to_image", dpi=200, use_page_numbers=True)
    
    # Interactive usage example
    print("\n=== Interactive Mode ===")
    while True:
        print("\n" + "="*50)
        print("PDF to Image Converter Menu:")
        print("1. Convert single PDF file")
        print("2. Convert folder of PDF files")
        print("3. List PDF files in a folder")
        print("4. Update settings")
        print("5. Show current settings")
        print("6. Universal converter (auto-detect)")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            pdf_path = input("Enter PDF file path: ").strip()
            if os.path.exists(pdf_path):
                output_folder = input(f"Output folder (press Enter for '{converter.output_folder}'): ").strip()
                output_folder = output_folder if output_folder else None
                
                dpi_input = input(f"DPI (press Enter for {converter.default_dpi}): ").strip()
                dpi = int(dpi_input) if dpi_input.isdigit() else None
                
                converter.convert_single(pdf_path, output_folder, dpi)
            else:
                print(f"File not found: {pdf_path}")
        
        elif choice == '2':
            folder_path = input("Enter folder path: ").strip()
            if os.path.exists(folder_path):
                output_folder = input(f"Output folder (press Enter for '{converter.output_folder}'): ").strip()
                output_folder = output_folder if output_folder else None
                
                dpi_input = input(f"DPI (press Enter for {converter.default_dpi}): ").strip()
                dpi = int(dpi_input) if dpi_input.isdigit() else None
                
                converter.convert_batch(folder_path, output_folder, dpi)
            else:
                print(f"Folder not found: {folder_path}")
        
        elif choice == '3':
            folder_path = input("Enter folder path to list PDF files: ").strip()
            converter.list_pdf_files(folder_path)
        
        elif choice == '4':
            print("\nUpdate Settings:")
            new_output = input(f"Output folder (current: '{converter.output_folder}'): ").strip()
            new_output = new_output if new_output else None
            
            new_dpi = input(f"DPI (current: {converter.default_dpi}): ").strip()
            new_dpi = int(new_dpi) if new_dpi.isdigit() else None
            
            use_pages = input(f"Use page numbers? (y/n, current: {converter.use_page_numbers}): ").strip().lower()
            if use_pages == 'y':
                new_use_pages = True
            elif use_pages == 'n':
                new_use_pages = False
            else:
                new_use_pages = None
            
            converter.update_settings(new_output, new_dpi, new_use_pages)
        
        elif choice == '5':
            settings = converter.get_settings()
            print("\nCurrent Settings:")
            for key, value in settings.items():
                print(f"  {key}: {value}")
        
        elif choice == '6':
            input_path = input("Enter PDF file or folder path: ").strip()
            if os.path.exists(input_path):
                output_folder = input(f"Output folder (press Enter for '{converter.output_folder}'): ").strip()
                output_folder = output_folder if output_folder else None
                
                dpi_input = input(f"DPI (press Enter for {converter.default_dpi}): ").strip()
                dpi = int(dpi_input) if dpi_input.isdigit() else None
                
                converter.convert(input_path, output_folder, dpi)
            else:
                print(f"Path not found: {input_path}")
        
        elif choice == '7':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")