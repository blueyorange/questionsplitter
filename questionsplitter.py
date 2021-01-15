from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw
import pytesseract

cwd = os.getcwd()
INPUT_FOLDER = os.path.join(cwd,'pdfs/Paper2')
OUTPUT_FOLDER = os.path.join(cwd,'output/')
filename = '570011-june-2019-question-paper-21.pdf'
# open file
os.chdir(INPUT_FOLDER)
print('Opening file...')
pageImages = convert_from_path(filename)
# select page
im = pageImages[12]
# set height and margins of page from example page
height = im.height
width = im.width
rightMargin = 100
bottomMargin = 125
top = 0
left = 0
qVerticalSep = 20
right = width-rightMargin
bottom = height-bottomMargin
pageBox = (top,left,right,bottom)

numberMargin = 200

leftMarginBox = (0,0,numberMargin,im.height)

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
    ''' Finds the horizontal start and end of regions of horizontal non-whitespace.
    Returns a list of tuples giving horizontal start and end of these regions.'''
    if rotate == True:
        im = im.rotate(90, expand=True)
    left = 0
    right = im.width
    top = 0
    bottom = im.height
    column_tuples = []
    white = (255,255,255,255)
    previous = 0
    for y in range(top,bottom):
        # line is one if any non-white pixels are detected
        current = 0
        for x in range(left, right):
            if im.getpixel((x,y))[0] != white:
                # non-white detected, store value and move on
                current = 1
                break
        if current == 1 and previous == 0:
            ystart = y
        if current == 0 and previous == 1:
            yend = y
            if rotate == False:
                column_tuples.append( (ystart, top, yend, bottom) )
            else:
                column_tuples.append( (top, ystart, bottom, yend) )
        previous = current
    return column_tuples

# crop left margin containing question numbers from main image
leftMarginImage = im.crop( leftMarginBox )
# Get coords of regions of non-whitespace
textBoundingBoxes = strips( leftMarginImage )
print(textBoundingBoxes)




'''
    # crop image to bounding box
    im = im.crop( boundingBox )
    # get x coords of strips, select question number strip
    numberColumn = strips(im, False)[0]
    # crop out the question numbers
    numColImage = im.crop( numberColumn )
    numberStrips = strips(numColImage, True)
    questionBoxes = []
    cropped_images = []

    n = len(numberStrips)
    for i in range(n):
        qleft = numberColumn[2]+left
        qtop = numberStrips[i][1]
        qright = right
        # check for last question
        if numberStrips[i] == numberStrips[-1]:
            qbottom = bottom
        else:
            qbottom = numberStrips[i+1][1] - qVerticalSep

        # Add bounding boxes of questions to list
        bbox = (qleft,qtop,qright,qbottom)

        # get rid of bottom whitespace
        cropped = im.crop(bbox)
        vertical_end = strips( cropped, True )[-1][3]
        new_bbox = (qleft+leftquestion,qtop,qright-rightquestion,qtop+vertical_end)
        questionBoxes.append( new_bbox )
    return questionBoxes

# output folder
os.chdir(OUTPUT_FOLDER)
# ignore cover page
pageImages.remove( pageImages[0] )
num = len(pageImages)
for pageImage in pageImages:
    n = pageImages.index(pageImage)
    boxes = getBoundingBoxes(pageImage,pageBox)
    draw = ImageDraw.Draw(pageImage)
    for box in boxes:
        draw.rectangle( box , outline='black')
    pageImage.save( 'p_{}.png'.format(n) )
'''