from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw, ImageFont
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
        if self.currentPage < len(self.pageImages):
            questions = self.getQuestionsFromPage(self.currentPage)
            self.currentPage += 1
            return questions
        else:
            raise StopIteration

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
                    question['image'] = im.crop( qBox )
                    # check for previous question on same page to amend qbox
                    if questions:
                        (x1,y1,x2,y2) = questions[-1]['qBox']
                        qBox = (x1,y1,x2,ystart-padding)
                        questions[-1]['qBox'] = qBox
                        questions[-1]['image'] = im.crop( qBox )
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

def extractAllQuestions(paper, removeNumbers=False):
    # iterate through pages
    pages = iter(paper)
    newImages = []
    for page in pages:
        for question in page:
            i = question['number']
            image = question['image']
            if removeNumbers==True:
                # Remove question numbers
                draw = ImageDraw.Draw(image)
                draw.rectangle(question['numBox'], fill='white')
            image.save('q_{}.png'.format(i))
        newImages.append(image)
    return newImages

def reNumberQuestions(paper):
    fontsFolder = 'usr/share/fonts'
    freeSansBoldFont = ImageFont.truetype(os.path.join(fontsFolder, 'FreeSansBold.ttf'),32)
    # q is the number of the question to be done consecutively
    q = 1
    old_q = 1
    remove_questions = [17,21,19]
    pages = iter(paper)
    pageImages = paper.pageImages
    p = 0
    for page in pages:
        print(page)
        for question in page:
            # blank out original question number
            draw = ImageDraw.Draw( pageImages[p] )
            (x1,y1,x2,y2) = question['numBox']
            draw.rectangle((x1,y1,x2,y2), fill='white')
            # renumber question
            qstr = str('{}.'.format(q))
            draw.text((x1,y1),qstr,fill='black', font=freeSansBoldFont)
            old_q +=1
            if old_q in remove_questions:
                draw.rectangle(question['qBox'],fill='white')
                q -= 1
            q += 1
        #pageImages[p].save('p_{}.pdf'.format(p))
        # Renumber pages
        width = pageImages[p].width
        draw.rectangle((0,0,width,175), fill='white')
        pageNumber = str(p+2)
        draw.text((width/2,80),pageNumber,fill='black', font=freeSansBoldFont)
        p += 1
    return pageImages

def main():
    # Define path variables
    cwd = os.getcwd()
    INPUT_FOLDER = os.path.join(cwd,'f4_exam')
    OUTPUT_FOLDER = os.path.join(cwd,'output/')
    filename = 'F4_exam.pdf'
    # create exam paper object from file
    os.chdir(INPUT_FOLDER)
    paper = ExamPaper(filename)
    # os.chdir(OUTPUT_FOLDER)
    images = reNumberQuestions(paper)
    firstPage = images[0]
    images.remove(firstPage)
    firstPage.save('renumbered.pdf', save_all=True, append_images=images)

if __name__ == "__main__":
    main()
