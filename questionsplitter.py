from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw
from pytesseract import image_to_string, image_to_data, Output

class ExamPaper:
    def __init__(self,filename):
        '''A class to extract data from an exam paper pdf'''
        self.filename = filename
        self.pageImages = convert_from_path(filename)
        self.pages={}
    
    def __iter__(self):
        self.currentPage = 0
        return self
    
    def __next__(self):
        page = self.page
        self.page += 1
        return page

    def getQuestionsFromPage(self,pageNumber):
        # get page data from this object
        print("Scanning page ", pageNumber)
        im = self.pageImages[pageNumber]
        pageHeight = im.height
        pageWidth = im.width
        # set defaults for page margins and bounding box padding
        top = 100
        left = 125
        numberWidth = 50
        right = pageWidth - 100
        bottom = pageHeight - 125
        padding = 8
        # above top of page is white
        wasBlack = 0
        # scan vertical lines for black pixels
        # List of dicts to store question details
        questions=[]
        for y in range(top,bottom):
            # line is one if any non-white pixels are detected
            isBlack = 0
            for x in range(left,left+numberWidth):
                if im.getpixel((x,y))[0] < 255:
                    # non-white detected, store value and move on
                    isBlack = 1
                    break
                else:
                    isBlack = 0
            if isBlack == 1 and wasBlack == 0:
                ystart = y-padding
            if isBlack == 0 and wasBlack == 1:
                # end of text area: record start and end of region as bounding box of number
                yend = y+padding
                numBox = (left,ystart,left+numberWidth,yend)
                qBox = (left,ystart,right,bottom)
                # estimate bounding box of question
                qNumber = containsNumber(im, numBox)
                if qNumber:
                    print("Found question ",qNumber)
                    # Create new dictionary for question
                    question = {}
                    # only append if actual question number
                    question['number'] = qNumber
                    question['numBox'] = numBox
                    question['qBox'] = qBox
                    # check for previous question on same page to amend qbox
                    if questions:
                        print("Found previous question. Amending box.")
                        (x1,y1,x2,y2) = questions[-1]['qBox']
                        questions[-1]['qBox'] = (x1,y1,x2,ystart-padding)
                        print(questions[-1]['qBox'])
                    questions.append(question)
            wasBlack = isBlack
        return questions
  
def containsNumber(im, box):
    image = im.crop(box)
    captured_string = image_to_string(image, config="--psm 10").strip()
    print( captured_string )
    if captured_string.isnumeric():
        return int(captured_string)
    else:
        return False

def main():
    # Define path variables
    cwd = os.getcwd()
    INPUT_FOLDER = os.path.join(cwd,'pdfs/Paper2')
    OUTPUT_FOLDER = os.path.join(cwd,'output/')
    filename = '570011-june-2019-question-paper-21.pdf'
    # open file
    os.chdir(INPUT_FOLDER)
    paper = ExamPaper(filename)
    questions = paper.getQuestionsFromPage(3)
    for q in questions:
        print('Found question ',q['number']," bbox ",q['qBox'])

if __name__ == "__main__":
    main()
