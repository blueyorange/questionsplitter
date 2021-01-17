from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw
from pytesseract import image_to_string, image_to_data, Output

def strips(im, box, padding=12):
    ''' Finds the horizontal start and end of regions of horizontal non-whitespace.
    Returns a list of tuples giving horizontal start and end of these regions.'''
    left = box[0]
    top = box[1]
    right = box[2]
    bottom = box[3]
    white = (255,255,255,255)
    previous = 0
    column_tuples = []
    for y in range(top,bottom):
        # line is one if any non-white pixels are detected
        current = 0
        for x in range(left, right):
            if im.getpixel((x,y))[0] < 255:
                # non-white detected, store value and move on
                current = 1
                break
        if current == 1 and previous == 0:
            ystart = y-padding
        if current == 0 and previous == 1:
            yend = y+padding
            column_tuples.append( (left,ystart,right,yend) )
        previous = current
    return column_tuples

def containsNumber(im, box):
    image = im.crop(box)
    captured_string = image_to_string(image, config="--psm 10").strip()
    print(captured_string)
    if captured_string.isnumeric():
        return True
    else:
        return False

def getQuestionBoxes(im, numberBoxes, pageBox, qVertSep = 20):
    qBoxes = []
    n = len(numberBoxes)
    for i in range(n):
        thisNumBox = numberBoxes[i]
        if i < (n-1):
            nextNumBox = numberBoxes[i+1]
        else:
            nextNumBox = None
        # determine bounding box of question from vertical position of question number
        # left edge is right edge of number box
        qleft = pageBox[0]
        qright = pageBox[2]
        qtop = thisNumBox[1]
        if nextNumBox:
            qbottom = nextNumBox[1]
        else:
            qbottom = pageBox[3]
        qBox = (qleft,qtop,qright,qbottom-qVertSep)
        qBoxes.append(qBox)
    return qBoxes

def main():
    # Define path variables
    cwd = os.getcwd()
    INPUT_FOLDER = os.path.join(cwd,'pdfs/Paper2')
    OUTPUT_FOLDER = os.path.join(cwd,'output/')
    filename = '570011-june-2019-question-paper-21.pdf'
    # open file
    os.chdir(INPUT_FOLDER)
    print('Opening file...',INPUT_FOLDER,filename)
    pageImages = convert_from_path(filename)
    # select page
    im = pageImages[12]
    # set height and margins of page from example page
    height = im.height
    width = im.width
    rightMargin = 100
    bottomMargin = 125
    topMargin = 0
    numberWidth = 70
    leftMargin = 115
    numberColumn = (leftMargin,topMargin,leftMargin+numberWidth,im.height-bottomMargin)
    pageBox = (leftMargin, topMargin, im.width-rightMargin, im.height-bottomMargin)
    textBoundingBoxes = strips( im,numberColumn )
    draw = ImageDraw.Draw(im)
    draw.rectangle( pageBox )
    draw.rectangle( numberColumn )
    for box in textBoundingBoxes:
        print(box)
        if containsNumber(im, box):
            draw.rectangle( box, outline = 'black' )
        else:
            draw.rectangle( box, outline = 'red' )
    os.chdir(OUTPUT_FOLDER)
    im.save('poo.png')
    '''
    print(textBoundingBoxes)
    # get bounding boxes of numbers from page
    numBoxes = getNumberBoxes(im, numberColumn)
    drawBoxes(im, numBoxes)
    draw = ImageDraw.Draw(im)
    # get bounding boxes of questions using number positions
    qBoxes = getQuestionBoxes(im,numBoxes,pageBox)
    drawBoxes(im, qBoxes)
    print(qBoxes)
    for qBox in qBoxes:
        draw.rectangle(qBox, outline='black')
        qImage = im.crop(qBox)
        string = image_to_string(qImage)
        print(string)
    os.chdir(OUTPUT_FOLDER)
    im.save('p.png')
'''
def justTessTry():
    '''A failed attempt to use just tesseract to get bounding boxes of numbers'''
   # Define path variables
    cwd = os.getcwd()
    INPUT_FOLDER = os.path.join(cwd,'pdfs/Paper2')
    OUTPUT_FOLDER = os.path.join(cwd,'output/')
    filename = '570011-june-2019-question-paper-21.pdf'
    # open file
    os.chdir(INPUT_FOLDER)
    print('Opening file...',INPUT_FOLDER,filename)
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
    numberMargin = 180
    leftMarginBox = (0,0,numberMargin,bottom)
    imMargin = im.crop( leftMarginBox )
    # get data from image using pytesseract
    d = image_to_data(imMargin, output_type=Output.DICT)
    n_boxes = len(d['level'])
    draw = ImageDraw.Draw(im)
    for i in range(n_boxes):
        box = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
        draw.rectangle(box, outline='black')
    im.save('tess.png')

if __name__ == "__main__":
    main()
