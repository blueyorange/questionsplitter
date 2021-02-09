from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
import os
from PIL import Image, ImageDraw, ImageFont
from pytesseract import image_to_string, image_to_data, Output
import re

class ExamPaper:
    def __init__(self, questionPaper, markScheme):
        '''A class to extract data from an exam paper pdf'''
        self.paperName = questionPaper.replace("QP","")
        self.questionPaperImages = convert_from_path(questionPaper)
        self.markSchemeImages = convert_from_path(markScheme)
        self.pages={}
    
    def __iter__(self):
        self.currentPage = 0
        return self
    
    def __next__(self):
        if self.currentPage < len(self.questionPaperImages):
            questions = self.getQuestionsFromPage(self.currentPage)
            self.currentPage += 1
            return questions
        else:
            raise StopIteration

    def readMS(self):
        im = self.markSchemeImages[1]
        text = image_to_string(im)
        answerRegEx = re.compile('\d+\s[ABCDc]')
        matches = answerRegEx.findall(text)
        answers = {match.split(" ")[0]:match.split(" ")[1].upper() for match in matches}
        answers = {str(i):answers[str(i)] for i in range(1,41)}
        return answers

    def getQuestionsFromPage(self,pageNumber):
        # get page data from this object
        print("Scanning page ", pageNumber)
        im = self.questionPaperImages[pageNumber]
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
                numBox = (left,ystart,left+numberWidth*2,yend)
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

def extractAllQuestions(paper, removeNumbers=True):

    return newImages

def reNumberQuestions(paper):
    fontsFolder = 'Users/russell/Library/Fonts/'
    freeSansBoldFont = ImageFont.truetype(os.path.join(fontsFolder, 'FreeSansBold.ttf'),32)
    freeSansFont = ImageFont.truetype(os.path.join(fontsFolder, 'FreeSans.ttf'),18)
    # q is the number of the question to be done consecutively
    q = 1
    old_q = 1
    remove_questions = [12,19]
    pages = iter(paper)
    questionPaperImages = paper.questionPaperImages
    p = 0
    for page in pages:
        print(page)
        for question in page:
            # blank out original question number
            draw = ImageDraw.Draw( questionPaperImages[p] )
            (x1,y1,x2,y2) = question['numBox']
            draw.rectangle((x1,y1,x2,y2), fill='white')
            # renumber question
            qstr = str('{}.'.format(q))
            draw.text((x1,y1),qstr,fill='black', font=freeSansBoldFont)
            if old_q in remove_questions:
                draw.rectangle(question['qBox'],fill='white')
                q -= 1
            old_q +=1
            q += 1
        #questionPaperImages[p].save('p_{}.pdf'.format(p))
        # Renumber pages
        width = questionPaperImages[p].width
        height = questionPaperImages[p].height
        # remove old pagenumbers and PMT reference
        draw.rectangle((0,0,width,175), fill='white')
        # remove copyright notice and question reference
        draw.rectangle((0,height-200,width,height), fill='white')
        pageNumber = str(p+2)
        draw.text((width/2,80),pageNumber,fill='black', font=freeSansBoldFont)
        # Add footer
        draw.text((200,height-150),'CONCORD COLLEGE IGCSE PHYSICS FORM 4 JANUARY EXAM 2021', fill='black', font=freeSansFont)
        p += 1
    return questionPaperImages

def main():
    # Define path variables
    cwd = os.getcwd()
    INPUT_FOLDER = os.path.join(cwd,'downloads/Paper1/')
    OUTPUT_FOLDER = os.path.join(cwd,'output/')
    # Get list of files
    os.chdir(INPUT_FOLDER)
    filenames = os.listdir()
    filenames.sort()
    # Change to output directory
    # Assume that filenames alternate questionpaper, mark scheme...
    # Iterate over all filenames
    for i in range(0,len(filenames),2):
        os.chdir(INPUT_FOLDER)
        # alphabetically, MS is before QP
        paper = ExamPaper(filenames[i+1],filenames[i])
        os.chdir(OUTPUT_FOLDER)
        os.mkdir(paper.paperName)
        os.chdir(paper.paperName)
        # Get answers from mark scheme
        answers = paper.readMS()
        # iterate through pages
        pages = iter(paper)
        # list of dicts to store information about each question in a single paper
        questions = []
        for page in pages:
            # page contains question data from a single page (no answer)
            for question in page:
                question['markscheme'] = answers[i]
                i = question['number']
                image = question['image']
                if removeNumbers==True:
                    # Remove question numbers
                    draw = ImageDraw.Draw(image)
                    draw.rectangle(question['numBox'], fill='white')
                image.save('q_{}.png'.format(i))
            print(page)
            questions.append(page)
        
        # write output
        print(questions)


    '''
    filename = 'F4_exam.pdf'
    # create exam paper object from file
    paper = ExamPaper(filename)
    # os.chdir(OUTPUT_FOLDER)
    images = reNumberQuestions(paper)
    firstPage = images[0]
    images.remove(firstPage)
    firstPage.save('renumbered_new.pdf', save_all=True, append_images=images)
    '''

if __name__ == "__main__":
    main()
