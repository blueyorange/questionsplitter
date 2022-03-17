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
import string
import json
import logging

RIGHT_MARGIN = 88
MARGINS = (120, 140, 1465, 2200)
NUMMARGIN = 55
INPUT_FOLDER = os.path.join(os.getcwd(), '')
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')
PROCESSED_FOLDER = os.path.join(os.getcwd(), 'processed')
COURSENAME = 'CIE IGCSE PHYSICS'
QUESTION_TYPE = 'extended'
logging.basicConfig(filename='logfile.txt',
                    encoding='utf-8', level=logging.DEBUG)


def cropMargins(images, margins):
    newImages = []
    for im in images:
        newImages.append(im.crop(margins))
    return newImages


def trimImage(im, vertPadding=10):
    imList = list(Image.Image.getdata(im))
    for i in range(len(imList)-1, 0, -1):
        if imList[i][0] != 255:
            y = int(i/im.width)
            im = im.crop((0, 0, im.width-1, y+vertPadding))
            return im


def getPageData(images, margin):
    ''' searches through paper for numbers in left hand margin (to left of margins[0])
    returns array of pages, each page is a dict containing an image of the page and an array containing question dicts'''
    # Reg Ex to look for numbers in strings (might have artifacts)
    numRe = re.compile('\d+')
    pages = []
    # iterate through pages
    for pageIndex, pageImage in enumerate(images):
        page = {}
        page['questions'] = []
        page['image'] = pageImage
        # crop out number margin to speed up number recognition
        croppedPage = pageImage.crop((0, 0, margin, pageImage.height))
        data = image_to_data(
            croppedPage, output_type=Output.DICT, config='--psm 6')
        # list to store words found in each question
        # iterate through each word found by tesseract
        for i, text in enumerate(data['text']):
            # ignore if not numeric
            numeric = numRe.findall(text)
            # get bounding box data
            left = data['left'][i]
            if not numeric:
                continue
            qNumber = numeric[0]
            if qNumber == 0:
                continue
            # ignore if question number not previous question number +1
            if page['questions']:
                if int(page['questions'][-1]['number']) != int(qNumber) - 1:
                    continue
            # create new question with question number bounding box
            question = {}
            question['numbox'] = (left, data['top'][i], data['left']
                                  [i]+data['width'][i], data['top'][i]+data['height'][i])
            question['number'] = qNumber
            page['questions'].append(question)
        pages.append(page)
    return pages


def getQuestions(pages, margin=NUMMARGIN, vertShift=10):
    questions = []
    for page in pages:
        im = page['image']
        n = len(page['questions'])
        if not page['questions']:
            # no question numbers on page, allocate whole page to previous question
            print('Found second image for question {}'.format(
                questions[-1]['number']))
            questions[-1]['images'].append(im.crop((0,
                                           0, im.width, im.height)))
        for i, question in enumerate(page['questions']):
            question['images'] = []
            (l, t, r, b) = question['numbox']
            if ((i == 0) and (t > 0.2 * im.height)):
                # if first question on page and
                # if y pos is greater than 10% of question region, append region above to previous question
                # as question from previous page spills on to this page
                print('2nd image detected, t={}'.format(t))
                questions[-1]['images'].append(im.crop((0, 0, im.width, t)))
            if i == n-1:
                # question is last on page
                question['box'] = (l+margin, t-vertShift, im.width, im.height)
            else:
                # question is not last on page so end box at next question
                question['box'] = (l+margin, t-vertShift, im.width,
                                   page['questions'][i+1]['numbox'][1]-vertShift)
            question['images'].append(im.crop(question['box']))
            questions.append(question)
    return(questions)


def extractMS(filename):
    ''' Reads a multiple choice mark scheme and returns dict of question number:answer'''
    # get list of images from path
    imageList = convert_from_path(filename)
    text = ""
    for im in imageList:
        # get text from page using pytesseract
        text = text + image_to_string(im, config='--psm 6')
    print("TEXT: "+text)
    # define RegEx and find matches
    answerRegEx = re.compile('\d+\s[ABCDc]')
    matches = answerRegEx.findall(text)
    answers = {match.split(" ")[0]: match.split(
        " ")[1].upper() for match in matches}
    #answers = {str(i):answers[str(i)] for i in range(1,41)}
    return answers


def saveImages(pageImages, path):
    firstPage = pageImages[0]
    pageImages.remove(firstPage)
    firstPage.save(path, save_all=True, append_images=pageImages)


def matchRegExes(string, regExes):
    '''Takes a string and a dict containing regexes and outputs a dict with the matches'''
    results = {}
    for key, value in regExes.items():
        regEx = re.compile(value)
        match = regEx.findall(string)[0]
        results[key] = match
    return results


def topic(string):
    topics = {'1.1 Length & Time': ['length', 'volume', 'time', 'clock'],
              '1.2 Motion': ['acceleration', 'velocity', 'deceleration'],
              '1.3 Mass and weight': ['mass', 'weight', 'planet'],
              '1.4 Density': ['density', 'float'],
              '1.5.1 Effects of Forces': ['force', 'extension', 'resultant', 'friction', 'circle', 'circular', 'spring'],
              '1.5.2-4 Turning effects': ['pivot', 'moment', 'centre', 'seesaw'],
              '1.5.5 Scalars and vectors': ['vector', 'scalar', 'magnitude'],
              '1.6 Momentum': ['momentum', 'impulse'],
              '1.7 Energy, work and power': ['kinetic', 'chemical', 'conservation', 'nuclear', 'renewable', 'work', 'power'],
              '1.8 Pressure': ['barometer', 'manometer', 'pressure'],
              '2.1 Simple kinetic molecular model of matter': ['solid', 'liquid', 'gas', 'particle', 'brownian', 'evaporation', 'gas'],
              '2.2 Thermal properties and temperature': ['temperature', 'thermometer', 'heat capacity', 'thermal', 'state'],
              '2.3 Thermal processes': ['conduction', 'convection', 'infrared'],
              '3.1 General wave properties': ['vibration', 'reflection', 'refraction', 'diffraction', 'wavelength', 'wave'],
              '3.2 Light': ['incidence', 'virtual', 'real', 'lens', 'lenses'],
              '3.3 Electromagnetic Spectrum': ['microwaves', 'infra-red', 'x-rays', 'electromagnetic'],
              '3.4 Sound': ['ultrasound', 'pitch', 'longitudinal', 'sound', 'echo'],
              '4.1 Magnetism': ['magnet', 'magnets', 'magnetism', 'magnetisation'],
              '4.2 Electrical quantities': ['charge', 'electrostatic', 'induction', 'volt', 'voltage', 'electrical'],
              '4.3 Electric circuits': ['circuit', 'lamp', 'resistance', 'current', 'thermistor', 'ldr'],
              '4.4 Digital electronics': ['logic', 'digital', 'analogue'],
              '4.5 Dangers of electricity': ['earth', 'earthing', 'live', 'fuse'],
              '4.6 Electromagnetic effects': ['e.m.f.', 'induced', 'transformer', 'motor'],
              '5.1 The nuclear atom ': ['protons', 'neutrons', 'proton', 'nuclide', 'isotope', 'oscilloscope'],
              '5.2 Radioactivity': ['bparticles', 'yrays', 'alpha', 'beta', 'gamma', 'background', 'decay', 'halflife', 'radioactive']}

    for topic, keywords in topics.items():
        for keyword in keywords:
            if keyword in string:
                return topic


def extractAllQuestions(questionPaper):
    regExes = {
        "year": r"\b\d{4}\b",
        "paper": r"Paper \d",
        "month": r"(\bJune|November|Specimen|March\b)"
    }
    filenameData = matchRegExes(questionPaper, regExes)
    print(filenameData)
    pageImages = convert_from_path(questionPaper)
    pageImages.pop(0)
    pageImages = cropMargins(pageImages, MARGINS)
    pageData = getPageData(pageImages, NUMMARGIN)
    questionData = getQuestions(pageData)
    for q in questionData:
        for i, im in enumerate(q['images']):
            q['images'][i] = trimImage(im)

        q.pop('box')
        q.pop('numbox')
        q['course'] = COURSENAME
        for key in filenameData:
            q[key] = filenameData[key]
        q['text'] = ""
        for im in q['images']:
            q['text'] += image_to_string(im)
        q['topic'] = topic(q['text'])
        q['type'] = QUESTION_TYPE
        if q['topic'] == "":
            n = q['number']
    return questionData


def checkQuestionArray(questions):
    # check that question number = index + 1, remove question if not
    for i, q in enumerate(questions):
        if i != int(q['number']) - 1:
            questions.remove(q)
        logging.warning(
            "Removed question from array as question number did not match index.")


def combineQuestionsAnswers(questions, answers):
    for q in questions:
        if q['number'] in answers:
            q['answer'] = answers[q['number']]
        else:
            n = q['number']
            q['answer'] = ""
    return questions


def dumpAllData(questions, dirname):
    os.mkdir(dirname)
    os.chdir(dirname)
    for q in questions:
        for i, im in enumerate(q['images']):
            fileprefix = 'Q{}_{}'.format(q['number'], i+1)
            im.save(fileprefix+'.png')
        q.pop('images')
    with open('data'+'.json', 'w') as fp:
        json.dump(questions, fp)


def sortFilesIntoTwoLists(filenames):
    print(filenames)
    questionPapers = []
    markSchemes = []
    for filename in filenames:
        print(filename)
        if 'QP' in filename:
            print(filename)
            questionPapers.append(filename)
        elif 'MS' in filename:
            markSchemes.append(filename)
        else:
            error = 'Non QP or MS file found.'
            logging.error('Non QP or MS file found.')
            print(error)
        print(questionPapers)
        print(markSchemes)
        questionPapers.sort()
        markSchemes.sort()
    if len(questionPapers) != len(markSchemes):
        logging.error(
            "Unequal lists of question papers and mark schemes. Aborting.")
        exit()
    return questionPapers, markSchemes


def extractFromFolder(folder):
    os.chdir(folder)
    filenames = os.listdir()
    print('{} files found'.format(len(filenames)))
    questionPaper = filenames[0]
    questions = extractAllQuestions(questionPaper)
    os.chdir(OUTPUT_FOLDER)
    dumpAllData(questions, "MS")


if __name__ == '__main__':
    extractFromFolder(INPUT_FOLDER)
