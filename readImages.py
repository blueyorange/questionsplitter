import os
from PIL import Image, ImageDraw, ImageFont
from pytesseract import image_to_string, image_to_data, Output

cwd = os.getcwd()
INPUT_FOLDER = os.path.join(cwd,'f4_exam/MS')
filenames = os.listdir(INPUT_FOLDER)
filenames.remove('.DS_Store')
print(filenames)
os.chdir(INPUT_FOLDER)
print("Opening file ",filenames[1])
im = Image.open(filenames[1])
text = image_to_string(im).strip()
print(text)
leftMargin = 185
numbersBox = (0,0,leftMargin,im.width)
numbersImage = im.crop(numbersBox)
numbers = image_to_data(numbersImage)
print(numbers)