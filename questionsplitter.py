from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw

cwd = os.getcwd()
INPUT_FOLDER = os.path.join(cwd,'pdfs/Paper2')
OUTPUT_FOLDER = os.path.join(cwd,'output/')
filename = '570011-june-2019-question-paper-21.pdf'

# open file
os.chdir(INPUT_FOLDER)
print('Opening file...')
images = convert_from_path(filename)
'''
# create output files
os.chdir(OUTPUT_FOLDER)
for image in images:
    image_number = str(images.index(image))
    file
    image.save('p'.join(image_number,'.png'))
    print(image.format)
    '''

def strips(im,rotate):
    ''' Finds the horizontal start and end of regions of vertical non-whitespace.
    Returns a list of tuples giving horizontal start and end of these regions.'''
    if rotate == True:
        im = im.rotate(90, expand=True)
    left=0
    right = im.width
    top = 0
    bottom = im.height
    column_tuples = []
    white = (255,255,255,255)
    previous = 0
    for x in range(left,right):
        # line is one if any non-white pixels are detected
        current = 0
        for y in range(top,bottom):
            if im.getpixel((x,y))[0] < 255:
                # non-white detected, store value and move on
                current = 1
                break
        if current == 1 and previous == 0:
            xstart = x
        if current == 0 and previous == 1:
            xend = x
            if rotate == False:
                column_tuples.append( (xstart, top, xend, bottom) )
            else:
                column_tuples.append( (top, xstart, bottom, xend) )
        previous = current
    return column_tuples

# select page
im = images[1]
# set height and margins of page
height = im.height
width = im.width
rightMargin = 100
bottomMargin = 125
top = 0
left = 0
right = width-rightMargin
bottom = height-bottomMargin
boundingBox = (top,left,right,bottom)
qVerticalSep = 20

# crop image to bounding box
im = im.crop( boundingBox )
# get x coords of strips, select question number strip
numberColumn = strips(im, False)[0]
print(numberColumn)
# crop out the question numbers
numColImage = im.crop( numberColumn )
numberStrips = strips(numColImage, True)
print(numberStrips)
questionBoxes = []

n = len(numberStrips)
for i in range(n):
    qleft = numberColumn[2]+left
    qtop = numberStrips[i][1]
    qright = right
    if numberStrips[i] == numberStrips[-1]:
        qbottom = bottom
    else:
        qbottom = numberStrips[i+1][1] - qVerticalSep

    questionBoxes.append( (qleft,qtop,qright, qbottom) )

im = images[1]


print(questionBoxes)
draw = ImageDraw.Draw(im)
for box in questionBoxes:
    draw.rectangle( box , outline='black')

os.chdir(OUTPUT_FOLDER)
im.save('p.png')
