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

MARGINS = (120,140,1550,2170)
NUMMARGIN = 55
INPUT_FOLDER = os.path.join(os.getcwd(),'downloads/Paper1')
OUTPUT_FOLDER = os.path.join(os.getcwd(),'output')
COURSENAME = 'CIE IGCSE PHYSICS'
logging.basicConfig(filename='logfile.txt',encoding='utf-8',level=logging.DEBUG)

def cropMargins(images,margins):
    newImages = []
    for im in images:
        newImages.append(im.crop(margins))
    return newImages

def trimImage(im,vertPadding=10):
    imList = list(Image.Image.getdata(im))
    for i in range(len(imList)-1,0,-1):
        if imList[i] < (255,255,255):
            y = int(i/im.width)
            im = im.crop((0,0,im.width-1,y+vertPadding))
            return im

def getPageData(images,margin):
    ''' searches through paper for numbers in left hand margin (to left of margins[0])
    returns array of pages, each page is a dict containing an image of the page and a dict of question data'''
    # Reg Ex to look for numbers in strings (might have artifacts)
    numRe = re.compile('\d+')
    pages = []
    # iterate through pages
    for pageIndex,pageImage in enumerate(images):
        page = {}
        page['questions'] = []
        page['image'] = pageImage
        # crop out number margin to speed up number recognition
        croppedPage = pageImage.crop( (0,0,margin,pageImage.height) )
        data = image_to_data(croppedPage, output_type=Output.DICT, config='--psm 6')
        # list to store words found in each question
        # iterate through each word found by tesseract
        for i, text in enumerate(data['text']):
            # ignore if not numeric
            numeric = numRe.findall(text)
            # get bounding box data
            left = data['left'][i]
            if not numeric: continue
            qNumber = numeric[0]
            if qNumber == 0: continue
            # create new question with question number bounding box
            question = {}
            question['numbox'] = (left,data['top'][i],data['left'][i]+data['width'][i],data['top'][i]+data['height'][i])
            question['number'] = qNumber
            page['questions'].append(question)
        pages.append(page)
    return pages

def getQuestions(pages,margin=NUMMARGIN, vertShift = 10):
    questions = []
    for page in pages:
        im = page['image']
        n = len(page['questions'])
        for i,question in enumerate(page['questions']):
            question['images'] = []
            (l,t,r,b) = question['numbox']
            if i == n-1:
                question['box'] = (l+margin,t-vertShift,im.width,im.height)
            else:
                question['box'] = (l+margin,t-vertShift,im.width,page['questions'][i+1]['numbox'][1]-vertShift)
            question['images'].append( im.crop(question['box']) )
            questions.append(question)
    return(questions)

def extractMS(filename):
    ''' Reads a multiple choice mark scheme and returns dict of question number:answer'''
    # get list of images from path
    imagelist = convert_from_path(filename)
    # answers are on second page
    im = imagelist[1]
    # get text from page using pytesseract
    text = image_to_string(im)
    # define RegEx and find matches
    answerRegEx = re.compile('\d+\s[ABCDc]')
    matches = answerRegEx.findall(text)
    answers = {match.split(" ")[0]:match.split(" ")[1].upper() for match in matches}
    answers = {str(i):answers[str(i)] for i in range(1,41)}
    return answers

def saveImages(pageImages, path):
    firstPage = pageImages[0]
    pageImages.remove(firstPage)
    firstPage.save(path, save_all=True, append_images=pageImages)

def matchRegExes(string,regExes):
    '''Takes a string and a dict containing regexes and outputs a dict with the matches'''
    results = {}
    for key,value in regExes.items():
        regEx = re.compile(value)
        match = regEx.findall(string)[0]
        results[key] = match
    return results

def topic(string):
    topics = {'1.1 Length & Time' : ['length','volume','time','clock'],
        '1.2 Motion' : ['acceleration','velocity','deceleration'],
        '1.3 Mass and weight' : ['mass','weight','planet'],
        '1.4 Density' : ['density','float'],
        '1.5.1 Effects of Forces' : ['force','extension','resultant','friction','circle','circular','spring'],
        '1.5.2-4 Turning effects' : ['pivot','moment','centre','seesaw'],
        '1.5.5 Scalars and vectors' : ['vector','scalar','magnitude'],
        '1.6 Momentum' : ['momentum','impulse'],
        '1.7 Energy, work and power': ['kinetic','chemical','conservation','nuclear','renewable','work','power'],
        '1.8 Pressure' : ['barometer','manometer','pressure'],
        '2.1 Simple kinetic molecular model of matter' : ['solid','liquid','gas','particle','brownian','evaporation','gas'],
        '2.2 Thermal properties and temperature' : ['temperature','thermometer','heat capacity','thermal','state'],
        '2.3 Thermal processes' : ['conduction','convection','infrared'],
        '3.1 General wave properties' : ['vibration','reflection','refraction','diffraction','wavelength','wave'],
        '3.2 Light' : ['incidence','virtual','real','lens','lenses'],
        '3.3 Electromagnetic Spectrum' : ['microwaves','infra-red','x-rays','electromagnetic'],
        '3.4 Sound' : ['ultrasound','pitch','longitudinal','sound','echo'],
        '4.1 Magnetism' : ['magnet','magnets','magnetism','magnetisation'],
        '4.2 Electrical quantities' : ['charge','electrostatic','induction','conductor','insulator','volt','voltage','electrical'],
        '4.3 Electric circuits' : ['circuit','lamp','resistance','current','thermistor','ldr'],
        '4.4 Digital electronics' : ['logic','digital','analogue'],
        '4.5 Dangers of electricity' : ['earth','earthing','live','fuse'],
        '4.6 Electromagnetic effects' : ['e.m.f.','induced','transformer','motor'],
        '5.1 The nuclear atom ' : ['protons','neutrons','proton','nuclide','isotope','oscilloscope'],
        '5.2 Radioactivity' : ['bparticles','yrays','alpha','beta','gamma','background','decay','halflife','radioactive']}
    
    finalTopic = ""
    for topic,keywords in topics.items():
        for keyword in keywords:
            if keyword in string:
                finalTopic = topic
    return finalTopic

def extractAllQuestions(questionPaper):
    regExes = {
    "year" : r"\b\d{4}\b",
    "paper" : r"Paper \d",
    "month" : r"(\bJune|November|Specimen\b)"
    }
    filenameData = matchRegExes(questionPaper,regExes)
    print(filenameData)
    pageImages = convert_from_path(questionPaper)
    pageImages.pop(0)
    pageImages = cropMargins(pageImages,MARGINS)
    pageData = getPageData(pageImages,NUMMARGIN)
    questionData = getQuestions(pageData)
    for q in questionData:
        for im in q['images']:
            im = trimImage(im)
        q.pop('box')
        q.pop('numbox')
        q['course'] = COURSENAME
        for key in filenameData:
            q[key] = filenameData[key]
        q['text'] = image_to_string(q['images'][0])
        q['topic'] = topic(q['text'])
    return questionData

def combineQuestionsAnswers(questions,answers):
    for q in questions:
        if answers[q['number']]:
            q['answer'] = answers[q['number']]
        else:
            logging.error("No answer found for question ",q['number'])
            q['answer'] = ""
    return questions

def dumpAllData(questions,dirname):
    os.mkdir(dirname)
    os.chdir(dirname)
    for q in questions:
        fileprefix = 'Q{}'.format(q['number'])
        for im in q['images']:
            im.save(fileprefix+'.png')
        q.pop('images')
        with open(fileprefix+'.json','w') as fp:
            json.dump(q, fp)

def extractFromFolder(folder):
    os.chdir(folder)
    filenames = os.listdir()
    filenames.sort()
    for i in range(0,len(filenames)-1,2):
        os.chdir(folder)
        questionPaper = filenames[i+1]
        dirname = os.path.splitext(questionPaper)[0]
        logging.info("Examining ",questionPaper)
        questions = extractAllQuestions(questionPaper)
        logging.info(len(questions)," extracted.")
        markScheme = filenames[i]
        answers = extractMS(markScheme)
        logging.info(len(answers), " answers extracted.")
        questions = combineQuestionsAnswers(questions,answers)
        os.chdir(OUTPUT_FOLDER)
        dumpAllData(questions,dirname)

extractFromFolder(INPUT_FOLDER)
