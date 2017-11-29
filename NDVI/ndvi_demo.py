#Cambio en el ajuste de blancos, con filtro red de infragram
#se agrego el ajuste del parametro brillo
#se ajusto los parametros antes de la toma de la foto
#Modifiction from 12/10/2016

import cv2
import numpy as np
import io
import picamera
import time
import sys
import math
import requests
#import displayTexto
import os.path
import os
from datetime import datetime

station = "ciat_"  
x = datetime.today().strftime("%Y-%m-%d")
ext = ".jpg"

file = open("conteo.txt","r")
w = file.readlines()

cuenta = int(w[1])

###Create a memory stream so photos doesn't need to be saved in a file
##stream = io.BytesIO()
##
###Get the picture (low resolution, so it should be quite fast)
###Here you can also specify other parameters (e.g.:rotate the image)
##with picamera.PiCamera() as camera:
##    camera.start_preview()
##    time.sleep(2)
##    camera.shutter_speed = 1000 #values in microseconds 0-6000000
##    camera.exposure_mode = 'off'
##    camera.iso = 100 #values between 0-800 
##    camera.awb_mode='off'
##    camera.awb_gains=(0.56,1.27)
##    camera.resolution = (1920, 1080)
##    #camera.resolution = (3280, 2464)
##    #camera.brightness = 20 #Values between 0-100
##    camera.capture(stream, format='png')
##    
###Convert the picture into a numpy array
##buff = np.fromstring(stream.getvalue(), dtype=np.uint8)
##
###Now creates an OpenCV image
##img = cv2.imdecode(buff, 1)
##cv2.imwrite('ngb.png',img)

#Recognize the number of photo (Four photos was captured)
if(cuenta==1):
    img = cv2.imread(station+x+ext,1)
if(cuenta==2):
    img = cv2.imread(str(cuenta)+station+x+ext,1)
if(cuenta==3):
    img = cv2.imread(str(cuenta)+station+x+ext,1)
if(cuenta==4):
    img = cv2.imread(str(cuenta)+station+x+ext,1)

#Reduction of size for improve the calculate more fast
img = cv2.resize(img,(0,0),fx=0.05,fy=0.05, interpolation = cv2.INTER_AREA)

#The order of matrix is in other different blue = [:,:,0], green = [:,:,1], red = [:,:,2]
#Suppose that NIR is in the channel blue by Rocco Filter

##---------
##Automatic adjust white balance in the image
##grayImage = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
##
##NIR = img[:,:,2]#get NIR band
##green = img[:,:,1]#get green band
##red = img[:,:,0]#get red band
##
##meanR = np.mean(red) #get the average of red
##meanG = np.mean(green)#get the average of green
##meanB = np.mean(NIR)#get average of NIR
##
##meanGray = np.mean(grayImage)#Get average of image gray scale 
##
##redChannel = np.uint8(red.astype(np.float32)*(meanGray/meanR))#Compute the adjust awb in the red channel by gray point
##greenChannel = np.uint8(red.astype(np.float32)*(meanGray/meanG))#Compute the adjust awb in the green channel by gray point
##blueChannel = np.uint8(NIR.astype(np.float32)*(meanGray/meanB))#Compute the adjust awb in the blue channel by gray point
##
##img = cv2.merge((redChannel,greenChannel,blueChannel)) #Concatenate the channels in one image.
##cv2.imwrite('ngbawb.jpg',img)


###-----
###Changing of color space in the image
##hsvImage = cv2.cvtColor(img,cv2.COLOR_RGB2HSV)
##
###get the Hue, Saturation and Value of the image
##H = hsvImage[:,:,0]
##S = hsvImage[:,:,1]
##V = hsvImage[:,:,2]
##
###Fix a gain for multiply with each array Hue, Saturation, Value
##gH = 1
##gS = 3.4
##gV = 1
##
###Execute multiply changing of value of each element of array
##H = np.uint8(np.round(H*gH))
##S = np.uint8(np.round(S*gS))
##V = np.uint8(np.round(V*gV))
##
###Concatenate again the array 
##hsvImage = cv2.merge((H,S,V))
##
###Return of color space RGB from HSV modified
##img= cv2.cvtColor(hsvImage,cv2.COLOR_HSV2RGB)
##cv2.imwrite('hsv2rgb.jpg',img)
#-------

#------------------Begin calculus of NDVI

# Get channels
NIR = img[:,:,0]
green = img[:,:,1]
red = img[:,:,2]

#Convert the matrix in floating point of 16 bits
g = green.astype(np.float16)
r = red.astype(np.float16)
nir = NIR.astype(np.float16)

# Parameters ELM
#Intercept with the y-axis

yG = 3.4815
yR = 3.5595
yNIR = 3.684

# Build Slope ELM

greenV = 75.551
redV = 78.799
nirV = 81.147

negLogG = -0.013272*greenV + yG
negLogR = -0.013433*redV + yR
negLogNIR = -0.01298*nirV + yNIR

mG = (negLogG - yG)/greenV
mR = (negLogR - yR)/redV
mNIR = (negLogNIR - yNIR)/nirV


#Transformation number digital DN to Reflectance value by ELM
nReflRed = mG*r + yG
nReflNIR = mNIR*nir + yNIR

ReflRed = np.exp(-1*nReflRed)
ReflNIR = np.exp(-1*nReflNIR)


# Tell numpy not to complain about division by 0:
np.seterr(invalid='ignore')
# calculate NDVI without correction
ndviWC = (ReflNIR-ReflRed)/(ReflNIR+ReflRed) 

# Brief correction NDVI
ndvi = 2.3329*ndviWC + 0.1756

#get width and height number rows and colums m: across n: horizontal
[m, n] = np.shape(ndvi)

# Get Max value of the NDVI matrix in terminal
ndviMAX = ndvi.max()
print("The max NDVI value is = "+repr(ndviMAX))

# Otsu's thresholding after Gaussian filtering

# Tell numpy not to complain about division by 0:
np.seterr(invalid='ignore')

ndviOtsu = (nir-r)/(nir+r)
NDVI_Otsu = np.uint8(127*(ndviOtsu+np.ones((m,n))))
blur = cv2.GaussianBlur(NDVI_Otsu,(21,21),0)
ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU)

#cv2.imwrite('ndviBinary33.jpg', th3)
# Segmentation

sumador=0.0 #Acumulate the value of sum of pixel by pixel in the image NDVI.
count=0.0 #Conut that there is pixel with value higher than 0.1 grow 1 unit.

for i in xrange(1, m):
    for j in xrange(1,n):
        if(th3[i,j]>1.0): #Contiditon or level for threshold
            if math.isnan(ndvi[i,j]):
                sumador = sumador + 0.0
            else:
                sumador = sumador + ndvi[i,j] #acumalate each value of pixel
                count= count + 1.0 #acumlate the count

ndviTrans = np.uint8(127*(np.asarray(ndvi)+np.ones((m,n)))) #Copy NDVI this way create other matrix with the same dimension
mediaNDVI = sumador/count #Apply the average of NDVI over plant
s = 'The mean NDVI by thresholding Otsu = ' + repr(mediaNDVI) 
NDVI = '{0:.2f}'.format(mediaNDVI)

fn ='/home/pi/ndvi.txt'

##if(os.path.exists(fn)):
##    file = open(fn,"a")
##    file.write(NDVI+"\n")
##    file.close
##
##else:
file = open(fn,"w")
file.write(NDVI+"\n")
file.close

# Conditional of count, only in one
if(cuenta==1):
    file = open("ndvi.txt","r")#Open ndvi.txt 
    w = file.readlines() #Read all lines
    #Send to thingspeak
    r = requests.get("http://labsistemas.javerianacali.edu.co:8002/update?key=JOCFHPCM97QJDRV4&field1="+w[0]+"&field2="+w[0]+"&field3="+w[0]+"&field4="+w[0])
    # Print in display if the send was corrected
    print (r.status_code, r.reason)
    os.remove('ndvi.txt')
    #cuenta = 0

# Elevate the counter
#cuenta = cuenta+1

# Write the file.txt with the new count
##file = open("conteo.txt","w")
##file.write("Cuenta"+"\n"+str(cuenta))
##file.close
    

#print('Value of NDVI sends to ThinkSpeak is '+NDVI)
# Send value NDVI to ThinkSpeak Portal
#r = requests.get("http://labsistemas.javerianacali.edu.co:8002/update?key=530P8TIFQFOZ2V00&field1="+NDVI)
#print s #Printing the value
#print (r.status_code, r.reason)

#-------

#displayTexto.verDisplay(NDVI)

#-------

#cv2.imwrite('ndviBinary33.jpg', th3)

##if(os.path.exists('/home/pi/'+station+x+ext)):
##    if(os.path.exists('/home/pi/1'+station+x+ext)):
##        if(os.path.exists('/home/pi/2'+station+x+ext)):
##            cv2.imwrite('3'+station+x+ext,ndviTrans)
##        else:
##            cv2.imwrite('2'+station+x+ext,ndviTrans)
##    else:
##        cv2.imwrite('1'+station+x+ext,ndviTrans)
##else:
##    cv2.imwrite(station+x+ext,ndviTrans)
##
##im_color = cv2.applyColorMap(ndviTrans, cv2.COLORMAP_JET)
##s2 = 'Average NDVI: ' + repr(round(mediaNDVI,3)) 
##font = cv2.FONT_HERSHEY_SIMPLEX
##cv2.putText(im_color,s2,(25,35), font, 1,(255,255,255),2)
##cv2.imwrite('ndviColor33.jpg',im_color)
quit() #Exit of the script
