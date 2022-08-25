import pytesseract
import pyautogui
import cv2
import numpy as np
import pandas as pd
import datetime

# variables
index = 0
new_code = True
flagscreenshot = 0
list_codes = []
list_status = []
list_description = []
bufferTimerScreenshot = 0
indexScreenshot = 0

# create a function that returns the text
def image_to_str(img):
    """ return a string from image """
    return pytesseract.image_to_string(img,lang='eng', config='--psm 6')

def screenshot_shooter(bufferTimerScreenshot,indexScreenshot):
    timerScreenshot = datetime.datetime.now()
    if ((timerScreenshot.second - bufferTimerScreenshot) > 1):
        screenshotstring_DTCscreen = "imagens/" + str(indexScreenshot) + ".jpg"
        cv2.imwrite(screenshotstring_DTCscreen, image)
        bufferTimerScreenshot = timerScreenshot.second
        print('disparou o screenshot')
        indexScreenshot += 1
        return bufferTimerScreenshot, indexScreenshot
    else:
        return bufferTimerScreenshot, indexScreenshot

# create a function that splits the DTC code into bytes
def byte_analysis(code):
    codeIdentifier = code[1]
    if (isinstance(codeIdentifier,int)):
        firstByte = "0x"
        letter = code[0]
        if letter == 'P':
            number_letter = 0
        elif letter == 'C':
            number_letter = 4
        elif letter == 'B':
            number_letter = 8
        else:
            number_letter = 12
        number = int(code[1])
        f_byte = str(hex(number_letter + number))
        secondByte = "0x"
        firstByte = f_byte + code[2]
        secondByte = secondByte + code[3] + code[4]
        print(firstByte, secondByte)
        return firstByte, secondByte
    else:
        return 'N/A','N/A'

# this function treats the data recieved by applying some filters
def treat_string(inputString):
    returnString = inputString
    returnString = returnString.replace("SENICIRC", "SEN/CIRC")
    returnString = returnString.replace("TCISC", "TC/SC")
    returnString = returnString.replace("SOLIV", "SOL/V")
    returnString = returnString.replace("INTIV", "INT/V")
    returnString = returnString.replace("EXHIV", "EXH/V")
    returnString = returnString.replace("KTR", "HTR")
    returnString = returnString.replace("Bt", "B1")
    returnString = returnString.replace("SCBWV", "SCB/V")
    returnString = returnString.replace("!", "I")
    returnString = returnString.replace("BIV", "B/V")
    returnString = returnString.replace("", "")
    return returnString

# this function treats the data recieved by applying some filters
def treat_string_code(inputString):
    returnString = inputString
    returnString = returnString.replace("SENICIRC", "SEN/CIRC")
    returnString = returnString.replace("O", "0")
    returnString = returnString.replace("TCISC", "TC/SC")
    returnString = returnString.replace("SCBWV", "SCB/V")
    returnString = returnString.replace("!", "I")
    returnString = returnString.replace("BIV", "B/V")
    returnString = returnString.replace("", "")
    return returnString


# this function does all the process of making a pandas dataframe out of the 5 images recieved
def process_image(frame, range_codex1, range_codex2, range_codey1, range_codey2, range_descriptionx1,
                  range_descriptionx2,
                  range_descriptiony1, range_descriptiony2, range_statusx1, range_statusx2, range_statusy1,
                  range_statusy2,
                  new_code, df, index, list_codes, list_status,bufferTimerScreenshot,indexScreenshot):
    code_frame = ''
    description_frame = ''
    status_frame = ''
    # selects the area of the region of interest of the image
    code_frame = frame[range_codex1:range_codex2, range_codey1:range_codey2]
    description_frame = frame[range_descriptionx1:range_descriptionx2, range_descriptiony1:range_descriptiony2]
    status_frame = frame[range_statusx1:range_statusx2, range_statusy1:range_statusy2]

    # converts the text in the image to a string
    code_text = image_to_str(code_frame)
    description_text = image_to_str(description_frame)
    status_text = image_to_str(status_frame)

    # filters the string removing the \n of it
    code_text = code_text.replace("\n", "")
    code_text = code_text.replace("o", "0")
    description_text = description_text.replace("\n", "")
    status_text = status_text.replace("\n", "")
    # checks for the same code
    if "CODE" in description_text:
        new_code = False
    if code_text == "":
        new_code = False
    for i in range(index):
        if ((code_text == list_codes[i]) & (description_text == list_description[i])):
            new_code = False
        elif (code_text == list_codes[i]):# & (status_text == "tt")):
            new_code = False

    # if its a new code, then enters the loop
    if (new_code == True):

        bufferTimerScreenshot, indexScreenshot = screenshot_shooter(bufferTimerScreenshot,indexScreenshot)

        byte0 = ''
        byte1 = ''
        list_codes.append(code_text)
        list_description.append(description_text)

        code_serie = pd.Series(code_text)
        description_serie = pd.Series(description_text)
        status_serie = pd.Series(status_text)
        if len(code_serie[0])>5:
            byte0, byte1 = byte_analysis(treat_string_code(code_serie[0]))

        df = df.append({'Code': treat_string_code(code_serie[0]), 'Description': treat_string(description_serie[0]),
                        'status': treat_string(status_serie[0]),'Byte 0': byte0, 'Byte 1': byte1}, ignore_index=True)
        index += 1
        flagscreenshot = 0
    return df, index, bufferTimerScreenshot, indexScreenshot


# defines the Tesseract-orc path
pytesseract.pytesseract.tesseract_cmd = r'tesseract-OCR\tesseract'

# creates a list with the csv headers
lista = [
    'Code',
    'Description',
    'status',
    'definir_ainda',
    'Byte 0',
    'Byte 1',
    'Byte 2'
]

# creates the panda dataframe with the headers
dataFrame = pd.DataFrame(columns=lista, dtype="string")
while (1):
    new_code = True
    flagscreenshot=1
    # takes a screenshot from the computer screen and turns it to a numpy array to be used
    image = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # saves the image in a png file
    cv2.imwrite("in_memory_to_disk.png", image)

    #treat the image for processing
    frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, frame = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    frame = cv2.GaussianBlur(frame, (3, 3), 0)
    cv2.imwrite('framu.jpg',frame)
    #cv2.waitKey(1)

    # calls the function process_image for the 5 DTC spaces
    dataFrame, index, bufferTimerScreenshot, indexScreenshot = process_image(frame, 250, 280, 29, 85, 250, 280, 106, 485, 250, 280, 540, 575, new_code,
                                     dataFrame,
                                     index, list_codes, list_status,bufferTimerScreenshot, indexScreenshot)
    dataFrame, index, bufferTimerScreenshot, indexScreenshot = process_image(frame, 310, 340, 29, 85, 310, 340, 106, 485, 310, 340, 540, 575, new_code,
                                     dataFrame,
                                     index, list_codes, list_status,bufferTimerScreenshot, indexScreenshot)
    dataFrame, index, bufferTimerScreenshot, indexScreenshot = process_image(frame, 370, 400, 29, 85, 370, 400, 106, 485, 370, 400, 540, 575, new_code,
                                     dataFrame,
                                     index, list_codes, list_status,bufferTimerScreenshot, indexScreenshot)
    dataFrame, index, bufferTimerScreenshot, indexScreenshot = process_image(frame, 430, 460, 29, 85, 430, 460, 106, 485, 430, 460, 540, 575, new_code,
                                     dataFrame,
                                     index, list_codes, list_status,bufferTimerScreenshot, indexScreenshot)
    dataFrame, index, bufferTimerScreenshot, indexScreenshot = process_image(frame, 490, 520, 29, 85, 490, 520, 106, 485, 490, 520, 540, 575, new_code,
                                     dataFrame,
                                     index, list_codes, list_status,bufferTimerScreenshot, indexScreenshot)
    dataFrame, index, bufferTimerScreenshot, indexScreenshot = process_image(frame, 550, 580, 29, 85, 550, 580, 106, 485, 550, 580, 540, 575, new_code,
                                     dataFrame,
                                     index, list_codes, list_status,bufferTimerScreenshot, indexScreenshot)
    dataFrame, index, bufferTimerScreenshot, indexScreenshot = process_image(frame, 610, 640, 29, 85, 610, 640, 106, 485, 610, 640, 540, 575, new_code,
                                     dataFrame,
                                     index, list_codes, list_status,bufferTimerScreenshot, indexScreenshot)

    # writes the csv file with the pandas dataFrame
    dataFrame.to_csv("dataFrame.csv")

input('Pressione ENTER para continuar....')