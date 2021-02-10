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
OUTPUT_FOLDER = os.path.join(os.getcwd(),'output')
os.chdir(INPUT_FOLDER)
filenames = os.listdir()
filenames.sort()
questionPaper = filenames[1]
markScheme = filenames[0]

def extractMS(filename):
    ''' Reads a multiple choice mark scheme and returns dict of question number:answer'''
    # get list of images from path
    imagelist = convert_from_path(filename)
    # answers are on second page
    im = imagelist[1]
    # get text from page using pytesseract
    text = image_to_string(im)
    print(text)
    # define RegEx and find matches
    answerRegEx = re.compile('\d+\s[ABCDc]')
    matches = answerRegEx.findall(text)
    print(matches.sort())
    answers = {match.split(" ")[0]:match.split(" ")[1].upper() for match in matches}
    answers = {str(i):answers[str(i)] for i in range(1,41)}
    print(answers)
    return answers

def getQuestionNumberBoxes(pages):
    '''Searches through a paper for question numbers and returns the page
    number and bounding boxes'''
    # set the width of the left margin in which to find question numbers
    numMargin = 170
    # Look for question 1 first
    max_number_width = 40
    max_number_height = 20
    # Reg Ex to look for numbers in strings (might have artifacts)
    numRe = re.compile('\d+')
    # iterate through pages
    questions = []
    tokens = []
    for pagenum,page in enumerate(pages):
        data = image_to_data(page, output_type=Output.DICT, config='--psm 6')
        # list to store words found in each question
        # iterate through each word found by tesseract
        for i, text in enumerate(data['text']):
            question = {}
            # ignore if not numeric
            numeric = numRe.findall(text)
            # store text as word if not empty string
            if text: tokens.append(text)
            # get bounding box data
            left = data['left'][i]
            # check for final token in list and append to current question if so
            if page == pages[-1]:
                questions[-1]['tokens'] = tokens
            # check for a number that is in the left margin
            if not numeric: continue
            if left > numMargin: continue
            # new question found: append word list to previous question if there is one
            if questions:
                questions[-1]['tokens'] = tokens
            tokens = []
            question['number'] = numeric[0]
            top = data['top'][i]
            right = left + data['width'][i]
            bottom = data['top'][i] + data['height'][i]
            box = (left,top,right,bottom)
            question['numbox'] = box
            question['page'] = pagenum
            questions.append(question)
            print(questions[-1])
    return questions

def removeQuestionNumbers(questions, pageImages):
    '''Iterates through each page drawing a white filled rectangle over the question numbers'''
    for question in questions:
        pageImage = pageImages[question['page']]
        print("Boxing question ",question['number'])
        draw = ImageDraw.Draw(pageImage)
        draw.rectangle(question['numbox'], fill='white')

def drawBoundingBoxes(questions, pageImages):
    '''Draws a box around each question'''
    for question in questions:
        pageImage = pageImages[question['page']]
        print("Boxing question ",question['number'])
        draw = ImageDraw.Draw(pageImage)
        draw.rectangle(question['box'], outline='red')
    
def getQuestionBoundingBoxes(questions, pageWidth, pageHeight):
    '''Takes the list of questions and works out a bounding box for each question
    based on the bounding box for each question number.'''
    last_item = len(questions)-1
    for i,this_question in enumerate(questions):
        last_question = (i==last_item)
        if not last_question:
            next_question = questions[i+1]
            last_question_on_page = (this_question['page']==next_question['page'])
            if not last_question_on_page:
                this_question['box'] = (this_question['numbox'][0],this_question['numbox'][1],
                    pageWidth-this_question['numbox'][0],next_question['numbox'][1]-10)
                continue
        # is last question or last question on page
        this_question['box'] = (this_question['numbox'][0],this_question['numbox'][1],
        pageWidth-this_question['numbox'][0],pageHeight-120)

def saveImages(pageImages, path):
    firstPage = pageImages[0]
    pageImages.remove(firstPage)
    firstPage.save(path, save_all=True, append_images=pageImages)

pageImages = convert_from_path(questionPaper)
pageWidth = pageImages[0].width
pageHeight = pageImages[0].height
questions = getQuestionNumberBoxes(pageImages)
#removeQuestionNumbers(questions,pageImages)
getQuestionBoundingBoxes(questions, pageWidth, pageHeight)
drawBoundingBoxes(questions, pageImages)
saveImages(pageImages,os.path.join(OUTPUT_FOLDER,questionPaper))
