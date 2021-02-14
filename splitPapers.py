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

def adjustBox(image,box,padding = 10):
    '''adjusts box dimensions to add vertical padding and remove whitespace from bottom'''
    (left,top,right,bottom) = box
    # search from bottom to first non-white pixel, row-by-row.
    for y in range(bottom-10,top,-1):
        for x in range(left,right):
            if image.getpixel((x,y)) < (255,255,255):
                print((x,y),image.getpixel((x,y)))
                return (left, top - padding, right + padding, y + padding)



def getQuestionData(pages):
    '''Searches through a paper for question numbers and returns the page
    number, question number, bounding boxes for the question number and the whole question,
    and a list of word tokens so that the question may be classified by content.'''
    # set the width of the left margin in which to find question numbers
    numMargin = 170
    # MIss out page footer
    bottomMargin = 170
    # Reg Ex to look for numbers in strings (might have artifacts)
    numRe = re.compile('\d+')
    # iterate through pages
    questions = []
    tokens = []
    question = {}
    prev_question = {}
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    for pagenum,page in enumerate(pages):
        data = image_to_data(page, output_type=Output.DICT, config='--psm 6')
        # list to store words found in each question
        # iterate through each word found by tesseract
        for i, text in enumerate(data['text']):
            question = {}
            # ignore if not numeric
            numeric = numRe.findall(text)
            # remove punctuation from token
            token = regex.sub('',text)
            # store text as word if not empty string
            if text: tokens.append(token)
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
            top = data['top'][i]-1
            right = left + data['width'][i]
            bottom = data['top'][i] + data['height'][i]
            box = (left,top,right,bottom)
            question['numbox'] = box
            question['page'] = pagenum
            # attach whole question bounding box info to previous question
            if questions:
                prev_question = questions[-1]
                if prev_question['page'] == question['page']:
                    # previous question is on same page
                    prev_question['box'] = adjustBox(page,(prev_question['numbox'][0],prev_question['numbox'][1],page.width-left,top))
                else:
                    # previous question is on different page so box ends at page bottom
                    prev_question['box'] = adjustBox(pages[questions[-1]['page']],(prev_question['numbox'][0],prev_question['numbox'][1],page.width-left,page.height-bottomMargin))
            print('Processed question ',question['number'],' on page ',question['page'])
            questions.append(question)
    if questions:
        # last question
        questions[-1]['box'] = adjustBox(pages[questions[-1]['page']],(questions[-1]['numbox'][0],questions[-1]['numbox'][1],page.width-prev_question['numbox'][0],page.height-bottomMargin))
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
        draw = ImageDraw.Draw(pageImage)
        draw.rectangle(question['box'], outline='red')

def saveImages(pageImages, path):
    firstPage = pageImages[0]
    pageImages.remove(firstPage)
    firstPage.save(path, save_all=True, append_images=pageImages)

def topics(tokens):
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
    
    topicList = []
    topic_result = None
    keyword_matches = []
    for topic,keywords in topics.items():
        for keyword in keywords:
            if keyword in tokens:
                keyword_matches.append(keyword)
                if topic not in topicList: topicList.append(topic)
                topic_result = topic
    return (topic_result,keyword_matches)

INPUT_FOLDER = os.path.join(os.getcwd(),'downloads/Paper1')
OUTPUT_FOLDER = os.path.join(os.getcwd(),'output')
os.chdir(INPUT_FOLDER)
# Retrieve list fo files from target folder and sort
filenames = os.listdir()
filenames.sort()
questionPaper = filenames[1]
print("Examining ",questionPaper)
markScheme = extractMS(filenames[0])
pageImages = convert_from_path(questionPaper)
questions = getQuestionData(pageImages)
# Save cropped question image and question data
os.chdir(OUTPUT_FOLDER)
# make directory with filename of paper
dirname = os.path.splitext(questionPaper)[0]
os.mkdir(dirname)
os.chdir(dirname)
# Add mark scheme answers and topic and keyword data to question list
for q in questions:
    q['answer'] = markScheme[q['number']]
    q['topic'],q['keywords'] = topics(q['tokens'])
    print(q['number'],q['topic'],q['keywords'])

    # crop image and remove question number
    im = pageImages[q['page']]
    draw = ImageDraw.Draw(im)
    draw.rectangle(q['numbox'], fill='white')
    cropped = im.crop(q['box'])
    fileprefix = 'Q{}'.format(q['number'])
    cropped.save(fileprefix+'.png')
    with open(fileprefix+'.json','w') as fp:
        json.dump(q, fp)

