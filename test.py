import pytesseract
from PIL import Image

def extract_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
    text = int(text.split("\n")[0].replace(' ',''))
    return text

print(extract_text("./data/credit_card.png"))