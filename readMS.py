from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw, ImageFont
from pytesseract import image_to_string, image_to_data, image_to_boxes, Output
import re

INPUT_FOLDER = os.path.join(os.getcwd(),'downloads/Paper1')
os.chdir(INPUT_FOLDER)
imagelist = convert_from_path('June 2003 MS - Paper 1 CIE Physics IGCSE.pdf')

im = imagelist[1]
text = image_to_string(im)
print(text)
