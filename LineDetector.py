# -*- coding: utf-8 -*-
import cv2 as cv
import numpy as np
from Sensor import LaneSensor

class LineDetector():
    def __init__(self, cropArea, sensorsNumber, sensorsWidth, lineStart, lineEnd, rightLineColorModel):
        self.lineSensors = []
        self.lineModel = None
        self.cropArea = None
        self.Initialize(cropArea, sensorsNumber, sensorsWidth, lineStart, lineEnd, rightLineColorModel)

    def Initialize(self, cropArea, sensorsNumber, sensorsWidth, lineStart, lineEnd, rightLineColorModel):
        self.cropArea = cropArea
        for iSensor in range(0, sensorsNumber):
            sensor = LaneSensor()
            pos = lineStart + iSensor*(lineEnd-lineStart)/(sensorsNumber+1)
            sensor.SetGeometry(pos, sensorsWidth)
            sensor.InitializeModel(rightLineColorModel.avgRGB, rightLineColorModel.avgHSV, (0.8318770212301404, 0.784796499543384, 0.6864621111668014), (41.02017792349725, 0.17449159984689502, 0.832041028240797))
            self.lineSensors.append(sensor) 
        self.lineModel = np.poly1d(np.polyfit([lineStart[1], lineEnd[1]], [lineStart[0], lineEnd[0]], 1)) 
    
    def ProcessFrame(self, img, hsv, canny, outputImg, outputFull, y1, width_crop):
        #sensors
        laneCoordinatesX = []
        laneCoordinatesY = []
        for sensor in self.lineSensors:
            linesNumber, lineSegments, allSegments = sensor.FindSegments(img, hsv, canny, outputImg, self.lineModel(sensor.yPos))
            if linesNumber == 1:
                sensor.UpdatePositionAndModelFromRegion(img, hsv, lineSegments[0])
                laneCoordinatesY.append((lineSegments[0][0]+lineSegments[0][1])/2)
                laneCoordinatesX.append(sensor.yPos)
    #        if linesNumber == 0:
    #            sensor.UpdatePositionBasedOnCanny(canny)
                
            sensor.UpdatePositionIfItIsFarAway(self.lineModel(sensor.yPos))
        
        if len(laneCoordinatesX)>0:
            rank = 'ok'
            try:
                z = np.polyfit(laneCoordinatesX, laneCoordinatesY, 1)
                #print np.polyfit(laneCoordinatesX, laneCoordinatesY, 1, None, True)
            except np.RankWarning:
                rank = 'bad'
                print "Line fiting problem"
            except:
                print 'URA!!!'
            if rank == 'ok':
                tmpLineModel = np.poly1d(z) 
                self.lineModel = tmpLineModel
            
            #self.lineModel = np.poly1d(np.polyfit(laneCoordinatesX, laneCoordinatesY, 1))
            for sensor in self.lineSensors:
                #cv.circle(outputImg, (laneCoordinatesX[i], laneCoordinatesY[i]), 2, [200, 0, 100], 2)
                cv.circle(outputImg, (int(self.lineModel(sensor.yPos)), sensor.yPos), 2, [100, 0, 200], 1)
        
        self.CheckLinePositionAndDrawOutput(outputFull, img, y1, width_crop)

    def CheckLinePositionAndDrawOutput(self, outputFull, img, y1, width_crop):
        testLineXOkColor = np.array([0,255,0])/1.0
        # testLineXOkColor = np.array([255,255,255])/30.5
        testLineXAlertColor = np.array([0,128,255])/1.0
        testLineXDangerColor = np.array([0,0,255])/1.0
        
        # testLeftLineXAlert = 530
        # testLeftLineXDanger = 730

        offset_ot_end_OK     = int(width_crop / 4)  # 25%
        offset_ot_end_Alert  = int(width_crop / 6)  # 15%
        offset_ot_end_Danger = int(width_crop / 10) # 10%

        testLeftLineXAlert = offset_ot_end_OK
        testLeftLineXDanger = offset_ot_end_OK + offset_ot_end_Alert
        testRightLineXDanger = offset_ot_end_OK + offset_ot_end_Alert + offset_ot_end_Danger
        testRightLineXAlert = offset_ot_end_OK + offset_ot_end_Alert + offset_ot_end_Danger + offset_ot_end_Alert

        testLeftLineY = y1 - 20
        # testLeftLineY = 100
        
        #find intersection of a lane edge and test line
        testLeftLineIntersection = int(self.lineModel(testLeftLineY))
        
        #make final output
        lanePosition = 'Ok'
        lanePositionColor = [0, 255, 0]
        if testLeftLineIntersection < img.shape[1]/2: 
            if testLeftLineXAlert < testLeftLineIntersection: 
                lanePosition = 'AlertLeft'
                lanePositionColor = testLineXAlertColor
            if testLeftLineXDanger < testLeftLineIntersection: 
                lanePosition = 'DangerLeft'
                lanePositionColor = testLineXDangerColor
        if testLeftLineIntersection > img.shape[1]/2: 
            if testLeftLineIntersection < testRightLineXAlert: 
                lanePosition = 'AlertRight'
                lanePositionColor = testLineXAlertColor
            if testLeftLineIntersection < testRightLineXDanger: 
                lanePosition = 'DangerRight'
                lanePositionColor = testLineXDangerColor
    
        #line model
        # cинии линии
        cv.line(outputFull, (self.cropArea[0]+int(self.lineModel(0)), self.cropArea[1]+0), (self.cropArea[0]+int(self.lineModel(img.shape[0])), self.cropArea[1]+img.shape[0]), [255, 0, 0], 2)        

        # Тонкая чёрная линия
        cv.line(outputFull, (self.cropArea[0],self.cropArea[1]+testLeftLineY) , (self.cropArea[0]+img.shape[1],self.cropArea[1]+testLeftLineY), [0.2,0.2,0.2])

        #zones L
        # левая зеленая линия
        cv.line(outputFull, (self.cropArea[0],self.cropArea[1]+testLeftLineY) , (self.cropArea[0]+testLeftLineXAlert,self.cropArea[1]+testLeftLineY), testLineXOkColor, 2)

        # левая оранжевая линия
        cv.line(outputFull, (self.cropArea[0]+testLeftLineXAlert,self.cropArea[1]+testLeftLineY) , (self.cropArea[0]+testLeftLineXDanger,self.cropArea[1]+testLeftLineY), testLineXAlertColor, 2)
        
        # левая красная линия
        cv.line(outputFull, (self.cropArea[0]+testLeftLineXDanger,self.cropArea[1]+testLeftLineY) , (self.cropArea[0]+img.shape[1]/2,self.cropArea[1]+testLeftLineY), testLineXDangerColor, 2)
      
    
        #zones R
        # правая зеленая линия
        cv.line(outputFull, (self.cropArea[0]+img.shape[1],self.cropArea[1]+testLeftLineY) , (self.cropArea[0]+testRightLineXAlert,self.cropArea[1]+testLeftLineY), testLineXOkColor, 2)
        
        # правая оранжевая линия
        cv.line(outputFull, (self.cropArea[0]+testRightLineXAlert,self.cropArea[1]+testLeftLineY), (self.cropArea[0]+testRightLineXDanger,self.cropArea[1]+testLeftLineY), testLineXAlertColor, 2)

        # правая красная линия
        cv.line(outputFull, (self.cropArea[0]+testRightLineXDanger,self.cropArea[1]+testLeftLineY), (self.cropArea[0]+img.shape[1]/2,self.cropArea[1]+testLeftLineY), testLineXDangerColor, 2)
        
  
        # круги на пересечинии синих линий и горизонтальной разноцветной линии
        cv.circle(outputFull, (self.cropArea[0]+testLeftLineIntersection, self.cropArea[1]+testLeftLineY), 2, lanePositionColor, 3)

        #alerts
        if lanePosition == 'AlertLeft' or lanePosition == 'DangerLeft':
            cv.line(outputFull, (img.shape[1]/2,50), (img.shape[1]/2-25,75), lanePositionColor, 15)
            cv.line(outputFull, (img.shape[1]/2,100), (img.shape[1]/2-25,75), lanePositionColor, 15)
        if lanePosition == 'DangerLeft':
            cv.line(outputFull, (img.shape[1]/2-30,50), (img.shape[1]/2-25-30,75), lanePositionColor, 15)
            cv.line(outputFull, (img.shape[1]/2-30,100), (img.shape[1]/2-25-30,75), lanePositionColor, 15)
        if lanePosition == 'AlertRight' or lanePosition == 'DangerRight':
            cv.line(outputFull, (img.shape[1]/2,50), (img.shape[1]/2+25,75), lanePositionColor, 15)
            cv.line(outputFull, (img.shape[1]/2,100), (img.shape[1]/2+25,75), lanePositionColor, 15)
        if lanePosition == 'DangerRight':
            cv.line(outputFull, (img.shape[1]/2+30,50), (img.shape[1]/2+25+30,75), lanePositionColor, 15)
            cv.line(outputFull, (img.shape[1]/2+30,100), (img.shape[1]/2+25+30,75), lanePositionColor, 15)
        
