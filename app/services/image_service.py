from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(file_path: str):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text