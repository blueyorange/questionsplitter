import os
from PIL import Image, ImageDraw, ImageFont
from pytesseract import image_to_string, image_to_data, image_to_boxes, Output

cwd = os.getcwd()
INPUT_FOLDER = os.path.join(cwd,'f4_exam/MS')
fontsFolder = 'usr/share/fonts'
filenames = os.listdir(INPUT_FOLDER)
filenames.remove('.DS_Store')
print(filenames)
os.chdir(INPUT_FOLDER)
freeSansFont = ImageFont.truetype(os.path.join(fontsFolder, 'FreeSans.ttf'),18)
images = []
for filename in filenames:
    print("Opening file ",filename)
    im = Image.open(filename)
    h = im.height
    w = im.width
    im = im.crop((0,0,w,h))
    print("Height ",h)
    leftMargin = 185
    qNumber = os.path.splitext(filename)[0]
    numbersBox = (0,0,leftMargin,im.width)
    numbersImage = im.crop(numbersBox)
    lines = image_to_boxes(numbersImage)
    print(lines)
    draw = ImageDraw.Draw(im)
    for line in lines:
        data = line.split(" ")
        character = data[0]
        (x,y,w,h) = tuple([int(data[i]) for i in range(1,5)])
        box = (x,y,w,h)
        if character.isnumeric():
            print("Found character ",character," replacing at ",(x,y-1500,w,h))
            draw.rectangle( box, fill='white')
            draw.text( (x,y),qNumber,fill='black', font=freeSansFont )
    im.save('{}_new.png'.format(qNumber))
    images.append(im)
    
# create new image
page = Image.new('RGB', (2480,3508),color='white')
pages = [page]
topMargin = 100
leftMargin = 100
bottomMargin = 100
padding = 20
current_ypos = topMargin
p=0
for image in images:
    if current_ypos + image.height > pages[p].height - bottomMargin:
        pages.append(Image.new('RGB', (2480,3508),color='white'))
        current_ypos=topMargin
        p += 1
    pages[p].paste( image, (leftMargin,current_ypos))
    current_ypos += image.height

print("Mark scheme created with ",p,"pages.")
firstPage = pages[0]
pages.remove(pages[0])
firstPage.save('F4_exam_MS.pdf', save_all=True, append_images=pages)