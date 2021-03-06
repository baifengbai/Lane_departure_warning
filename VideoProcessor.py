# -*- coding: utf-8 -*-
import cv2 as cv
from LaneMarkersModel import LaneMarkersModel
from LaneMarkersModel import normalize
import numpy as np
from Sensor import LaneSensor
from LineDetector import LineDetector

from optparse import OptionParser 

def draw_canny_edges(binary_mask, img):
    return draw_binary_mask(binary_mask, img)

def gimp_to_opencv_hsv(*hsv):
    """
    I use GIMP to visualize colors. This is a simple
    GIMP => CV2 HSV format converter.
    """
    return (hsv[0] / 2, hsv[1] / 100 * 255, hsv[2] / 100 * 255)

# A fixed polygon coordinates for the region of interest
ROI_VERTICES = np.array([[(50, 540), (420, 330), (590, 330), 
                    (960 - 50, 540)]], dtype=np.int32)    

# White and yellow color thresholds for lines masking.
# Optional "kernel" key is used for additional morphology
WHITE_LINES = { 'low_th': gimp_to_opencv_hsv(0, 0, 80),
                'high_th': gimp_to_opencv_hsv(359, 10, 100) }
#
# YELLOW_LINES = { 'low_th': gimp_to_opencv_hsv(35, 20, 30),
#                 'high_th': gimp_to_opencv_hsv(65, 100, 100),
#                 'kernel': np.ones((3,3),np.uint64)}

# WHITE_LINES = { 'low_th':  gimp_to_opencv_hsv(281, 27, 100),
#                 'high_th': gimp_to_opencv_hsv(291, 98, 100),
#                 'kernel': np.ones((3,3), np.uint64) }

# WHITE_LINES = { 'low_th':  gimp_to_opencv_hsv(281, 27, 100),
#                 'high_th': gimp_to_opencv_hsv(291, 98, 100) }
                # 'high_th': gimp_to_opencv_hsv(359, 10, 100) }
                # 'high_th': gimp_to_opencv_hsv(284, 97, 100) }

# YELLOW_LINES = { 'low_th': gimp_to_opencv_hsv(35, 20, 30),
#                 'high_th': gimp_to_opencv_hsv(65, 100, 100),
#                 'kernel': np.ones((3,3),np.uint64)}


def get_lane_lines_mask(hsv_image, colors):
    """
    Image binarization using a list of colors. The result is a binary mask
    which is a sum of binary masks for each color.
    """
    masks = []
    for color in colors:
        if 'low_th' in color and 'high_th' in color:
            mask = cv.inRange(hsv_image, color['low_th'], color['high_th'])
            if 'kernel' in color:
                mask = cv.morphologyEx(mask, cv.MORPH_OPEN, color['kernel'])
            masks.append(mask)
        else: raise Exception('High or low threshold values missing')
    if masks:
        return cv.add(*masks)


def draw_binary_mask(binary_mask, img):
    if len(binary_mask.shape) != 2: 
        raise Exception('binary_mask: not a 1-channel mask. Shape: {}'.format(str(binary_mask.shape)))
    masked_image = np.zeros_like(img)
    for i in range(3): 
        masked_image[:,:,i] = binary_mask.copy()
    return masked_image



# Разбор опций командной строки
parser = OptionParser() 
parser.add_option("-i", "--input", dest="input_video", help="", default="video/in/video_in.mp4")  
parser.add_option("-o", "--output", dest="output_video", help="", default="video/out/out_video.mp4")  
(options, args) = parser.parse_args() 


# Входной поток видео
stream = cv.VideoCapture(options.input_video) #6 7 8
if stream.isOpened():
    # width = stream.get(cv.CV_CAP_PROP_FRAME_WIDTH)   # float
    # height = stream.get(cv.CV_CAP_PROP_FRAME_HEIGHT) # float
    #
    # # or
    width = stream.get(3)  # float
    height = stream.get(4) # float
    #
    # # it gives me 0.0 :/
    # fps = vcap.get(cv2.cv.CV_CAP_PROP_FPS)
	# print width
	# print 'The value of PI is approximately {}.'.format(math.pi)
    print 'Ширина {}'.format(height)
    print width
else:
    print "Cannot open input video"
    exit()


# Выходной поток видео
videoWriter = cv.VideoWriter(options.output_video, cv.VideoWriter_fourcc(*'MJPG'), 30, (1280, 720), 1)


''' 
Вычислим рабочую область в которой будет происходить основое действие
В этой области будем искать сенсорами разметку
'''

# x1 = int(width/4) 
# y1 = int(height/2)
# x2 = int(x1*3)
# y2 = int(height)

x1 = int(width/9) 
y1 = int(height/2)
x2 = int(width)
y2 = int(height)

# x1 = int(width/6) 
# y1 = int(height/3) * 2
# x2 = int(width - width/9)
# y2 = int(height)


# x1 = 140
# y1 = int(height/2)
# x2 = width
# y2 = int(height)

# print x1, y1, x2, y2
#
''' Ширина области для построения радужной линии '''
width_crop  = x2 - x1
# height_crop = y2 - y1

# размер области захвата видео для определения полос
# cropArea = [x1, y1, x2, y2]
#
# (0,0)|
#  ----|----------------------->
#      |  (x1,y1)
#      | *____________ 
#      | |            |
#      | |            |
#      | |            |
#      | |            |
#      | |            |
#      | |            |
#      | -------------* (x2,y2)
#      |
#
# cropArea = [0, 124, 637, 298] # для видео 640*480
# cropArea = [0, 250, 1240, 645]  # для видео 1280*720
cropArea = [x1, y1, x2, y2]  # для видео 1280*720
sensorsNumber = 50
sensorsWidth = 70

# #6L
# line1LStart = np.array([35, 128])
# line1LEnd = np.array([220, 32])
# #
# #6R
# line1RStart = np.array([632, 146])
# line1REnd = np.array([476, 11])

# # расположение синих линий на видео в координатах
# #L
# line1LStart = np.array([x1 + 35, y1 + 300])
# line1LEnd = np.array([x1 + 220, y1 + 100])
# #
# #R
# line1RStart = np.array([x1 + 632, y1 + 300])
# line1REnd = np.array([x1 + 476, y1 + 100])

# расположение синих линий на видео в координатах
#L
line1LStart = np.array([35, 300])
line1LEnd = np.array([220, 100]) #100
#
#R
line1RStart = np.array([932, 300])
line1REnd = np.array([776, 100])

# расположение синих линий на видео в координатах
#L
# line1LStart = np.array([35, height_crop - int(height_crop/9)])
# line1LEnd = np.array([int(width/2) - 55, int(height_crop/9)])
# # line1LEnd = np.array([int(width_crop/2) - 55, int(height_crop/9)])
# #
# #R
# line1RStart = np.array([int(width_crop/2) + 35, int(height_crop/9)])
# line1REnd = np.array([width_crop - 35, height_crop - int(height_crop/9)])


#get first frame for color model
# flag, imgFull = stream.read()
# img = imgFull[cropArea[0]:cropArea[2], cropArea[1]:cropArea[3]]
# img = imgFull[cropArea[1]:cropArea[3], cropArea[0]:cropArea[2]]

#Initialize left lane
leftLineColorModel = LaneMarkersModel()
#leftLineColorModel.InitializeFromImage(np.float32(img)/255.0, "Select left line")
leftLine = LineDetector(cropArea, sensorsNumber, sensorsWidth, line1LStart, line1LEnd, leftLineColorModel)

#Initialize right lane
rightLineColorModel = LaneMarkersModel()
#rightLineColorModel.InitializeFromImage(np.float32(img)/255.0, "Select right line")
rightLine = LineDetector(cropArea, sensorsNumber, sensorsWidth, line1RStart, line1REnd, rightLineColorModel)

frameNumber = 0
while(cv.waitKey(1) != 27): # пока не нажат esc
    frameNumber+=1
    print frameNumber
    
    # захватываем текущий кадр и кладем его в переменную img
    flag, imgFull = stream.read()
    if flag == False: break #end of video





    #do some preprocessing to share results later
    img = np.float32(imgFull[cropArea[1]:cropArea[3], cropArea[0]:cropArea[2]])/255.0
   
    # # # меняем цветовую модель на HSV
    hsv = np.float32(cv.cvtColor(img, cv.COLOR_RGB2HSV))
    hsv = cv.GaussianBlur(hsv, (25, 25), 2)

    canny = cv.Canny(cv.cvtColor(np.uint8(img*255), cv.COLOR_RGB2GRAY), 0, 170, 0)
    # canny = cv.Canny(cv.cvtColor(np.uint8(img*255), cv.COLOR_RGB2GRAY), 70, 170)





    # hsv = np.float32(cv.cvtColor(img, cv.COLOR_RGB2HSV))
    #
    # # binary_mask = get_lane_lines_mask(hsv, [WHITE_LINES, YELLOW_LINES])
    # binary_mask = get_lane_lines_mask(hsv, [WHITE_LINES, WHITE_LINES ])
    #
    # masked_image = draw_binary_mask(binary_mask, hsv)
    #
    # blank_image = np.zeros_like(img)
    #
    # canny = cv.Canny(np.uint8(masked_image), 0, 170, 10)
    # # canny = cv.Canny(np.uint8(masked_image), 0, 170)
    #
    # # canny = draw_canny_edges(edges_mask, blank_image)
    #





    #make output images
    outputImg = img.copy()
    outputFull = imgFull.copy()
    outputHSV = hsv.copy()
    outputCANNY = canny.copy()
    
    # outputMask = masked_image.copy()
    # outputBinary = binary_mask.copy()

    #process frame
    leftLine.ProcessFrame(img, hsv, canny, outputImg, outputFull, y1, width_crop)
    rightLine.ProcessFrame(img, hsv, canny, outputImg, outputFull, y1, width_crop)
    
    
    #show output
    cv.imshow("Output", outputImg)
    cv.imshow("Output full", outputFull)
    cv.imshow("Output hsv", outputHSV)
    cv.imshow("Output canny", outputCANNY)

    # cv.imshow("Output mask", outputMask)
    # cv.imshow("Output binary", outputBinary)
    
    #write output
    videoWriter.write(outputFull)
    
cv.destroyAllWindows()
