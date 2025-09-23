from PIL import Image, ImageOps
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def process_image(image_field, max_width, max_height, format='JPEG', quality=85):
    """
    Process and optimize an uploaded image.

    Args:
        image_field: Django ImageField instance
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        format: Output format (JPEG or PNG)
        quality: JPEG quality (1-100)

    Returns:
        InMemoryUploadedFile: Processed image
    """
    if not image_field:
        return image_field

    # Open the image
    img = Image.open(image_field)

    # Convert RGBA to RGB if saving as JPEG
    if format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
        # Create a white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
        img = background

    # Calculate the target size while maintaining aspect ratio
    img.thumbnail((max_width * 2, max_height * 2), Image.Resampling.LANCZOS)

    # Use ImageOps.fit for smart cropping to exact dimensions
    img = ImageOps.fit(
        img,
        (max_width, max_height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5)
    )

    # Save the processed image to a BytesIO object
    output = io.BytesIO()

    # Set format-specific save parameters
    save_kwargs = {'format': format}
    if format == 'JPEG':
        save_kwargs['quality'] = quality
        save_kwargs['optimize'] = True

    img.save(output, **save_kwargs)
    output.seek(0)

    # Create a new InMemoryUploadedFile
    return InMemoryUploadedFile(
        output,
        'ImageField',
        f"{image_field.name.split('.')[0]}.{format.lower()}",
        f'image/{format.lower()}',
        sys.getsizeof(output),
        None
    )


def process_category_image(image_field):
    """
    Process category images to 800x600px (4:3 ratio).

    Args:
        image_field: Django ImageField instance

    Returns:
        InMemoryUploadedFile: Processed image optimized for categories
    """
    return process_image(image_field, 800, 600, format='JPEG', quality=85)


def process_product_image(image_field):
    """
    Process product images to 600x600px (1:1 ratio).

    Args:
        image_field: Django ImageField instance

    Returns:
        InMemoryUploadedFile: Processed image optimized for products
    """
    return process_image(image_field, 600, 600, format='JPEG', quality=85)


def validate_image_size(image_field, max_size_mb=5):
    """
    Validate that an uploaded image doesn't exceed the maximum file size.

    Args:
        image_field: Django ImageField instance
        max_size_mb: Maximum allowed size in megabytes

    Returns:
        tuple: (is_valid, error_message)
    """
    if not image_field:
        return True, None

    max_size_bytes = max_size_mb * 1024 * 1024

    if image_field.size > max_size_bytes:
        return False, f"Image file size must be less than {max_size_mb}MB"

    return True, None


def validate_image_format(image_field):
    """
    Validate that an uploaded image is in an acceptable format.

    Args:
        image_field: Django ImageField instance

    Returns:
        tuple: (is_valid, error_message)
    """
    if not image_field:
        return True, None

    try:
        img = Image.open(image_field)
        if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
            return False, "Please upload a valid image file (JPEG, PNG, GIF, or WEBP)"
        image_field.seek(0)  # Reset file pointer after checking
        return True, None
    except Exception:
        return False, "Invalid image file"