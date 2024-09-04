import base64
from PIL import Image
import io
import os
from typing import Optional, Dict, Any

class ImageProcessor:
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    def encode_image_to_base64(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Encode an image file to base64.

        Args:
        image_path (str): The path to the image file.

        Returns:
        Optional[Dict[str, Any]]: A dictionary containing the base64 encoded image and its MIME type,
                                  or None if there was an error.
        """
        try:
            # Check if the file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Check if the file format is supported
            file_extension = os.path.splitext(image_path)[1].lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"Unsupported image format: {file_extension}")

            # Open the image file
            with Image.open(image_path) as img:
                # Convert image to RGB if it's in RGBA mode
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # Create a byte stream
                byte_arr = io.BytesIO()
                # Save the image to the byte stream in JPEG format
                img.save(byte_arr, format='JPEG')
                # Get the byte string
                byte_arr = byte_arr.getvalue()

            # Encode the byte string to base64
            base64_encoded = base64.b64encode(byte_arr).decode('utf-8')

            # Determine MIME type
            mime_type = f"image/{file_extension[1:]}"  # Remove the dot from file extension
            if file_extension in {'.jpg', '.jpeg'}:
                mime_type = "image/jpeg"

            return {
                "base64_image": base64_encoded,
                "mime_type": mime_type
            }

        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return None

    def get_image_metadata(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an image file.

        Args:
        image_path (str): The path to the image file.

        Returns:
        Optional[Dict[str, Any]]: A dictionary containing image metadata,
                                  or None if there was an error.
        """
        try:
            # Check if the file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Open the image file
            with Image.open(image_path) as img:
                # Get basic image information
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                }

                # Get EXIF data if available
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = {
                        Image.TAGS[k]: v
                        for k, v in img._getexif().items()
                        if k in Image.TAGS
                    }
                    exif_data = {k: str(v) for k, v in exif.items()}

                metadata["exif"] = exif_data

                return metadata

        except Exception as e:
            print(f"Error getting image metadata: {str(e)}")
            return None

    def resize_image(self, image_path: str, output_path: str, size: tuple) -> bool:
        """
        Resize an image and save it to a new file.

        Args:
        image_path (str): The path to the input image file.
        output_path (str): The path where the resized image will be saved.
        size (tuple): The desired size as a tuple of (width, height).

        Returns:
        bool: True if the operation was successful, False otherwise.
        """
        try:
            with Image.open(image_path) as img:
                resized_img = img.resize(size)
                resized_img.save(output_path)
            return True
        except Exception as e:
            print(f"Error resizing image: {str(e)}")
            return False
