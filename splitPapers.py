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

def getQuestionNumberBoxes(filename):
    '''Searches through a paper for question numbers and returns the page
    number and bounding boxes'''
    # set the width of the left margin in which to find question numbers
    numMargin = 170
    # Look for question 1 first
    current_question = 1
    numRe = re.compile('\d+')
    imagelist = convert_from_path(filename)
    im = imagelist[1]
    data = image_to_data(im, output_type=Output.DICT)
    print(data)
    # iterate through tesseract data
    results = []
    for i, value in enumerate(data):
        # ignore if no numerical digits found
        numeric = numRe.findall(data['text'][i])
        print(data['text'][i])
        if not numeric: continue
        left = data['left'][i]
        top = data['top'][i]
        right = data['top'][i] + data['width'][i]
        bottom = data['top'][i] + data['height'][i]
        box = (left,top,right,bottom)
        print(numeric,box)


getQuestionNumberBoxes(questionPaper)