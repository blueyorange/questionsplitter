from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os

cwd = os.getcwd()
INPUT_FOLDER = os.path.join(cwd,'pdfs/')
OUTPUT_FOLDER = os.path.join(cwd,'output/')
filename = 'June 2003 QP - Paper 3 CIE Physics IGCSE.pdf'

# open file
os.chdir(INPUT_FOLDER)
print('Opening file...')
images = convert_from_path(filename)

# create output files
os.chdir(OUTPUT_FOLDER)
for image in images:
    image_number = str(images.index(image))
    image.save('p'.join(image_number,'.png'))
    print(image.format)