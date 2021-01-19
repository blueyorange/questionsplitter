from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw
from pytesseract import image_to_string, image_to_data, Output

def getNumBoxes(imageList, box, numMargin, OUTPUT_FOLDER, padding=8):
    os.chdir(OUTPUT_FOLDER)
    left=box[0]
    top=box[1]
    right=box[0]+numMargin
    bottom=box[3]
    output_list = []
    for im in imageList:
        # ignore first page
        if imageList.index(im)==0:
            continue
        pageNo = imageList.index(im)
        draw = ImageDraw.Draw(im)
        previous = 0
        for y in range(top,bottom):
            questions=[]
            # line is one if any non-white pixels are detected
            current = 0
            for x in range(left,right):
                if im.getpixel((x,y))[0] < 255:
                    # non-white detected, store value and move on
                    current = 1
                    break
            if current == 1 and previous == 0:
                ystart = y-padding
            if current == 0 and previous == 1:
                yend = y+padding
                numBox = (left,ystart,right,yend)
                if output_list[-1]['page'] == pageNo:
                    # previous question is on same page need to alter box
                    (x1,y1,x2,y2) = 
                    output_list[-1]['qbox'][3] = ystart - padding
                qBox = (left,ystart,right,bottom)
                qNumber = containsNumber(im, numBox)
                if qNumber:
                    # only append if actual question number
                    qdict['number'] = qNumber
                    qdict['numBox'] = numBox
                    qdict['qBox'] = qBox
                    qdict['page'] = pageNo
                    qdict['pageImage'] = im
                    output_list.append(qdict)
                    draw.rectangle(numBox, fill = 'white')
            previous = current
            '''
        if qdict['page'] and qdict['page']!=pageNo:
            # no question number found on page: grab whole page and add to question
            # get previous question number as this is part of that question
            qdict['number'] = output_list[-1]['number']
            qdict['numBox'] = box
            qdict['page'] = pageNo
            output_list.append(qdict)
        '''
        im.save('p_{}.png'.format(pageNo))
    n = len(output_list)
    # cycle through list and create question boxes
    for i in range(n-1):
        this_dict = output_list[i]
        this_page = this_dict['page']
        (x1,y1,x2,y2) = this_dict['numBox']
        if i<n:
            next_dict = output_list[i+1]
            next_page = next_dict['page']
            (x3,y3,x4,y4) = next_dict['numBox']
        if this_page == next_page or i==n:
            # another question on page: make y-end of bounding box top of next
            this_dict['qBox'] = (x1,y1,box[2],y3-10)
        else:
            # last question on page: make bottom of page end of question
            this_dict['qBox'] = (x1,y1,box[2],box[3])
        # crop image and save
        this_dict['qImage'] = this_dict['pageImage'].crop(this_dict['qBox'])
        this_dict['qImage'].save('q_{}.png'.format(this_dict['number']))
    return output_list

def containsNumber(im, box):
    image = im.crop(box)
    captured_string = image_to_string(image, config="--psm 10").strip()
    if captured_string.isnumeric():
        return int(captured_string)
    else:
        return False

def getQuestionBoxes(im, numberBoxes, pageBox, qVertSep = 20):
    qBoxes = []
    # Return page box if no number on page (question must carry over from previous page)
    if not numberBoxes:
        return [pageBox]
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
    im = pageImages[1]
    # set height and margins of page from example page
    rightMargin = 100
    bottomMargin = 125
    topMargin = 100
    numberWidth = 50
    leftMargin = 125
    pageBox = (leftMargin, topMargin, im.width-rightMargin, im.height-bottomMargin)
    print(pageBox)
    textBoundingBoxes = getNumBoxes(pageImages, pageBox,numberWidth, OUTPUT_FOLDER)

if __name__ == "__main__":
    main()
