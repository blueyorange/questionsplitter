from pytesseract import image_to_string, image_to_data, image_to_boxes, Output
import re
from pdf2image import convert_from_path

def extractMS(filename):
    ''' Reads a multiple choice mark scheme and returns dict of question number:answer'''
    # get list of images from path
    imageList = convert_from_path(filename)
    text = ""
    for im in imageList:
        # get text from page using pytesseract
        text = text + image_to_string(im,config='--psm 11')
    print("TEXT: "+text)
    # define RegEx and find matches
    answerRegEx = re.compile('\d+\s[ABCDc]')
    matches = answerRegEx.findall(text)
    answers = {match.split(" ")[0]:match.split(" ")[1].upper() for match in matches}
    #answers = {str(i):answers[str(i)] for i in range(1,41)}
    return answers

if __name__ == '__main__':
    extractMS('/Users/russ/Projects/questionsplitter/downloads/Paper2/multiple choice/November 2017 (v1) MS - Paper 2 CIE Physics IGCSE.pdf')