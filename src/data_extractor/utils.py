import base64
import os
import io
import time
from pathlib import Path
from PIL import Image

def compress_image_for_api(image_path: str) -> str:
    """
    Only compress PNG if it exceeds 5MB limit. Uses PNG-only compression methods.
    Returns base64 string of image
    """
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    OPTIMAL_LONG_EDGE = 1568  # Anthropic's recommended max dimension
    
    try:
        # Check original file size first
        original_size = os.path.getsize(image_path)
        
        # Base64 encoding increases size by ~33%, so check if encoded size will exceed limit
        # Use 3.75MB threshold (3.75 * 1.33 ≈ 5MB)
        SAFE_SIZE_BEFORE_BASE64 = int(MAX_SIZE_BYTES * 0.75)  # 3.75MB
        
        # If under safe threshold, return original without modification
        if original_size <= SAFE_SIZE_BEFORE_BASE64:
            with open(image_path, "rb") as f:
                original_b64 = base64.b64encode(f.read()).decode("utf-8")
            size_mb = original_size / (1024 * 1024)
            encoded_size_mb = len(original_b64) * 3 / 4 / (1024 * 1024)  # Approximate decoded size
            print(f"  ✅ Original size {size_mb:.2f}MB (encoded: ~{encoded_size_mb:.2f}MB) - no compression needed")
            return original_b64
        
        # File is too large, need to compress
        print(f"  ⚠️ Original size {original_size / (1024 * 1024):.2f}MB exceeds 5MB - compressing PNG...")
        
        with Image.open(image_path) as img:
            original_mode = img.mode
            
            # Step 1: Try optimize + compress_level=9 on original size
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            # Check base64 size (the actual size that will be sent)
            compressed_data = buffer.getvalue()
            base64_size = len(base64.b64encode(compressed_data))
            
            if base64_size <= MAX_SIZE_BYTES:
                compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
                size_mb = base64_size / (1024 * 1024)
                print(f"  ✅ Compressed to {size_mb:.2f}MB base64 (PNG optimize + compress_level=9)")
                return compressed_b64
            
            # Step 2: Try resizing to optimal dimension
            width, height = img.size
            max_dimension = max(width, height)
            
            if max_dimension > OPTIMAL_LONG_EDGE:
                scale_factor = OPTIMAL_LONG_EDGE / max_dimension
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                print(f"  Resized from {width}x{height} to {new_size[0]}x{new_size[1]}")
                
                buffer = io.BytesIO()
                img_resized.save(buffer, format='PNG', optimize=True, compress_level=9)
                buffer.seek(0)
                
                # Check base64 size
                compressed_data = buffer.getvalue()
                base64_size = len(base64.b64encode(compressed_data))
                
                if base64_size <= MAX_SIZE_BYTES:
                    compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
                    size_mb = base64_size / (1024 * 1024)
                    print(f"  ✅ Compressed to {size_mb:.2f}MB base64 (PNG resized + optimized)")
                    return compressed_b64
                
                img = img_resized  # Use resized for next steps
            
            # Step 3: Try color quantization (24-bit → 8-bit, 256 colors)
            # This is still PNG, just with fewer colors
            print(f"  Applying color quantization (256 colors)...")
            if img.mode != 'P':  # Only quantize if not already palettized
                img_quantized = img.quantize(colors=256)
            else:
                img_quantized = img
            
            buffer = io.BytesIO()
            img_quantized.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            # Check base64 size
            compressed_data = buffer.getvalue()
            base64_size = len(base64.b64encode(compressed_data))
            
            if base64_size <= MAX_SIZE_BYTES:
                compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
                size_mb = base64_size / (1024 * 1024)
                print(f"  ✅ Compressed to {size_mb:.2f}MB base64 (PNG 256-color)")
                return compressed_b64
            
            # Step 4: Emergency - more aggressive resize
            print(f"  ⚠️ Applying emergency resize (50%)...")
            width, height = img.size
            new_size = (int(width * 0.5), int(height * 0.5))
            img_emergency = img.resize(new_size, Image.Resampling.LANCZOS)
            
            if img_emergency.mode != 'P':
                img_emergency = img_emergency.quantize(colors=256)
            
            buffer = io.BytesIO()
            img_emergency.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            compressed_data = buffer.getvalue()
            compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
            
            size_mb = len(compressed_b64) / (1024 * 1024)
            print(f"  Final size: {size_mb:.2f}MB base64 (PNG 50% resize + 256 colors)")
            return compressed_b64
            
    except Exception as e:
        print(f"  ❌ Error processing image: {e}")
        # Last resort: try original image
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

def find_equipment_images(pmt_number: str, image_dir: str = 'converted_to_image') -> list:
    """
    Find all PNG images for a given PMT number with flexible matching
    """
    image_files = []
    current_dir = Path(image_dir)
    
    # Remove spaces and special characters for flexible matching
    clean_pmt = pmt_number.replace(' ', '').replace('-', '').replace('_', '').lower()
    
    for pattern in ['*.png', '*.jpg', '*.jpeg']:
        for file_path in current_dir.rglob(pattern):
            clean_filename = file_path.stem.replace(' ', '').replace('-', '').replace('_', '').lower()
            
            if clean_pmt in clean_filename:
                image_files.append(file_path)
    
    # Remove duplicates
    image_files = list(set(image_files))
    image_files.sort()
    
    return image_files

def get_equipment_number_from_image_path(image_path: str) -> str:
    """
    Extract equipment number from image file path
    Assumes filename format: MLK PMT 10107 - H-001_page_002.png
    where MLK PMT 10107 is the PMT number and H-001 is the equipment number
    Returns equipment number as string  
    """
    filename = Path(image_path).stem  # Get filename without extension
    parts = filename.split('_page_')[0]  # Remove page suffix if present
    segments = parts.split(' - ')
    if len(segments) < 2:
        return ""
    equipment_part = segments[1]  # e.g. H-001
    return equipment_part.strip().replace(' ', '')
    
if __name__ == "__main__":
    # Example usage
    test_image_path = "converted_to_image\\MLK PMT 10101 - V-001_page_002.png"
    
    eq_number = get_equipment_number_from_image_path(test_image_path)
    print(f"Extracted Equipment Number: {eq_number}")