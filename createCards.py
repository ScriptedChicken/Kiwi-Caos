import time
start = time.time()

# import libraries
import xml.etree.ElementTree as element_tree
import textwrap
import json
import csv
from PIL import Image, ImageDraw
from cairosvg import svg2png
import os

class CardCreator():
    def __init__(self):
        self.title = ''
        self.code = ''
        self.description = ''
        self.background = ''
        self.row = None
        self.numberOfCards = None
        self.cardQueue = []
        self.i = 0

    def setCsvPath(self, path):
        self.reader = csv.reader(open(path, "r"), delimiter=",")

    def setSvgTemplatePath(self, path):
        self.cardTemplate = element_tree.parse(path)
        self.cardTemplateRoot = self.cardTemplate.getroot()
    
    def setLangauge(self, language):
        langaugeCodeDict = {
            "english":"en",
            "spanish":"es"
        }
        self.languageCode = langaugeCodeDict[language]
    
    def setConfigPath(self, path):
        with open(path, 'r') as f:
            rawConfig = json.load(f)
            self.config = rawConfig[self.languageCode]
        
    def setCardValues(self):
        cardName = self.row[0]
        cardType = self.row[1]
        cardDesc = self.row[2]
        numberOfCards = self.row[3]
        cardColour = self.config[cardType]["colour"]
        if type(cardColour) == dict:
            climaType = cardName.lower()
            cardColour = cardColour[climaType]
        cardCode = self.config[cardType]["code"]
        self.cardValues = {
            'Title': cardName,
            'Code': cardCode,
            'Description': cardDesc,
            'Background': cardColour,
            'NumberOfCards': numberOfCards
        }

    def createDescription(self):
        self.obj.text = ''
        children = self.obj.getchildren()
        line_count = 0
        desc = self.cardValues['Description']
        lines = textwrap.wrap(desc,35)
        for child in children:
            try:
                line = lines[line_count]
                child.text = line
            except:
                child.text = ''
            line_count += 1

    def createImage(self):
        if self.languageCode == 'es':
            name = self.cardValues['Title']
        else:
            rawName = self.cardValues['Title']
            name = self.config["imageNameDict"][rawName]
        name = name.replace(" ", "_").lower()
        img_path = os.getcwd() + f"/img/{name}.jpg"
        self.obj.attrib[r'{http://www.w3.org/1999/xlink}href'] = img_path

    def setBackground(self):
        style = self.obj.attrib['style']
        styles = style.split(';')
        new_style = ''
        for s in styles:
            data = s.split(':')
            key = data[0]
            value = data[1]
            if key == 'fill':
                value = self.cardValues["Background"]
            
            new_style += f'{key}:{value};'
        new_style = new_style[:-1]
        self.obj.attrib['style'] = new_style

    def setOtherValue(self):
        id = self.obj.attrib['id']
        text = self.cardValues[id]
        self.obj.text = text

    def setTitle(self):
        title_len = len(self.obj.text)
        style = self.obj.attrib['style']
        styles = style.split(';')
        new_style = ''
        for s in styles:
            data = s.split(':')
            key = data[0]
            value = data[1]
            if key == 'font-size' and title_len <= 18:
                value = '13px'
            if key == 'font-size' and 18 < title_len < 23:
                value = '12px'
            if key == 'font-size' and 23 <= title_len:
                value = '10px'
            
            new_style += f'{key}:{value};'
        new_style = new_style[:-1]
        self.obj.attrib['style'] = new_style

    def searchTemplate(self):
        for obj in self.cardTemplateRoot.iter():
            try:
                # print(obj.attrib['id'])
                self.obj = obj
                if obj.attrib['id'] == "Description":
                    self.createDescription()
                elif obj.attrib['id'] == "CardImage":
                    self.createImage()
                elif obj.attrib['id'] in ["Circle_Background", "Title_Background"]:
                    self.setBackground()
                else:
                # print(obj.text)
                    self.setOtherValue()
                    # print(obj)
                if obj.attrib['id'] == "Title":
                    self.setTitle()

            except Exception as e:
                # print(e)
                pass

    def createPng(self):
        cardName = self.cardValues['Title']
        cardName = cardName.replace(' ', '_')
        self.svgPath = os.path.join("svg",f"{cardName}.svg")
        self.pngPath = os.path.join("png",f"{cardName}.png")
        self.cardTemplate.write(self.svgPath)
        svg2png(open(self.svgPath, 'r').read(), write_to=self.pngPath)
        os.remove(self.svgPath)

    def queueCard(self):
        numberOfCards = int(self.cardValues["NumberOfCards"])
        for num in range(numberOfCards):
            self.cardQueue.append(self.pngPath)

    def generateCards(self):
        i = 0
        for row in self.reader:
            if i != 0:
                self.row = row
                del row

                self.setCardValues()
                self.searchTemplate()
                self.createPng()
                self.queueCard()
            i += 1

    
    def createCardSheets(self):
        card_template = Image.open(r'templados/sheet_template.png','r')

        # get the image size
        x,y = card_template.size

        ncol = 3
        nrow = 4

        page_no = 1
        template = Image.new('RGB',(x*ncol,y*nrow))
        size_counter = 0
        for i, card in enumerate(sorted(self.cardQueue)):
            px, py = x*int(size_counter/nrow), y*(size_counter%nrow)
            template.paste(Image.open(card),(px,py))
            size_counter += 1
        
            filename = f'page_{page_no}.png'

            if (i != 0 and i % 12 == 0) or i == len(self.cardQueue) - 1:
                path = os.path.join('card sheets',self.languageCode,filename)
                template.save(path,format='png')
                page_no += 1
                size_counter = 0
                template = Image.new('RGB',(x*ncol,y*nrow))

    def cleanup(self):
        self.cardQueue = []
        path = "./png"
        for f in os.listdir(path):
            os.remove(os.path.join(path,f))

    def createBackings(mode="PROD"):
        backingsDict = {
            "acción":"dibujo_atras_acción.png",
            "clima":"dibujo_atras_clima.png"
        }

        for cardType, filename in backingsDict.items():
            path = os.path.join('templados', filename)
            card_template = Image.open(path,'r')

            # get the image size
            x,y = card_template.size

            ncol = 3
            nrow = 4

            page_no = 1
            template = Image.new('RGB',(x*ncol,y*nrow))
            size_counter = 0
            i = 0
            while i != 12:
                px, py = x*int(size_counter/nrow), y*(size_counter%nrow)
                template.paste(card_template,(px,py))
                size_counter += 1
                i += 1
            
                if i != 0 and i % 12 == 0:
                    template.save(f'hoja_{cardType}.png',format='png')
                    page_no += 1
                    size_counter = 0
                    # break

    def createGrid(self):
        height = 800
        width = 800
        image = Image.new(mode='L', size=(height, width), color=255)

        # Draw some lines
        draw = ImageDraw.Draw(image)
        y_start = 0
        y_end = image.height
        step_size = int(image.width / 15)

        for x in range(0, image.width, step_size):
            line = ((x, y_start), (x, y_end))
            draw.line(line, fill=128)

        x_start = 0
        x_end = image.width

        for y in range(0, image.height, step_size):
            line = ((x_start, y), (x_end, y))
            draw.line(line, fill=128)

        del draw

        image.show()
        image.save("tabla.png")

cardCreator = CardCreator()

# en
cardCreator.setLangauge('english')
cardCreator.setCsvPath("Cards.csv")
cardCreator.setSvgTemplatePath("templados/dibujo.svg")
cardCreator.setConfigPath("config.json")
cardCreator.generateCards()
cardCreator.createCardSheets()
# cardCreator.cleanup()

end = time.time()

print(f"Script completed in {round(end-start,2)} seconds")