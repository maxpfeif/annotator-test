from flask import Flask
from flask import render_template
from flask import make_response
from flask import request
import cv2 as cv
import json
import numpy as np
#enables display of detailed error reports for debugging. Remove this when the program is ready for launch
import cgitb
cgitb.enable()

#might need to import the rect function 

alpha = 1.0 #simple brightness control, ranges from 0.5 to 2.5 in 0.1 steps.
# img_path = 'sample.jpg' #image path used everywhere in script
img_path = 'volvoExample.png' #sample image path
img = cv.imread(img_path)
disp_W = 600 #width to size displayed images to 
disp_H = 330 #height to size displayed images to 
img = cv.resize(img, (disp_W, disp_H))
zoom = 1 #keeps track of our zoom power

app = Flask(__name__)

#initialize the HTML page upon launching the script. 
@app.route('/')
def index():
    return render_template('index.html')

#method that returns the state to the client, has some parent dependencies. 
def responder():
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response  

#Primary Zoom Execution method. 
#   Takes a boolean "zoom" which is true if in, false if out.
#   Needs a center position to zoom at, X and Y.  
#   Returns the result, as a new image, resized to global standard. 
def zoomer(x, y):
    #calculate new image width (rel to original)
    zoom_W = disp_W/(2**zoom)
    zoom_H = disp_H/(2**zoom)
    #define X1, X2, Y1, Y2 from zoom and center points
    X1 = x-(zoom_W/2)
    Y1 = y-(zoom_H/2)
    X2 = x+(zoom_W/2)
    Y2 = y+(zoom_H/2)
    #now generate clipped region 
    roi = img[Y1:Y2, X1:X2]
    roi = cv.resize(roi, (disp_W, disp_H), 0,0,1)
    return roi  

#intial and original image update module 
@app.route('/image', methods = ['GET', 'POST'])
def image():
    global img
    img = cv.imread(img_path)
    img = cv.resize(img, (disp_W, disp_H))
    if request.method == "POST":
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
        cv.threshold(img, 140, 255, 0, img) 
    #reset the contrast and zoom when returning to original state
    global alpha     
    alpha = 1.0 
    global zoom
    zoom = 1
    return responder()

#an attempt at resizing, to 2X zoomed in same location now. 
@app.route('/zoom_in')
def zoom_in():
    global img
    global zoom
    if (zoom < 3):
        zoom +=1
    mousex = 160
    mousey = 120
    img = zoomer(mousex,mousey)
    return responder()

@app.route('/zoom_out')
def zoom_out():
    global img
    global zoom   
    if (zoom > 0):
        zoom -=1
    if (zoom == 0):
        mousex = disp_W/2
        mousey = disp_H/2
    else: 
        #replace these with the mouse position 
        mousex = disp_W/3
        mousey = disp_H/3
    img = zoomer(mousex,mousey)
    return responder()

#simple method for processing edge detection. 
@app.route('/egde')
def edge():
    global img
    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    img = cv.Canny(img,50,150)
    #makes sure the zoom is reflective of current state with edges on
    img = zoomer()
    return responder()

#this module incriments the contrast
@app.route('/contrast_plus')
def contrast_plus():
    global alpha 
    global img
    if alpha < 2.0:
        alpha += 0.1
    #iterate through the pixels and multiply the individual pixel values by the constrast adjusting aplha
    img[:,:,0] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,0]]
    img[:,:,1] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,1]]
    img[:,:,2] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,2]]
    return responder()
   
#this module decriments the image contrast 
@app.route('/contrast_minus')
def contrast_minus():
    global alpha
    global img
    if alpha > 0.5:
        alpha -= 0.1
    #iterate through the pixels and multiply the individual pixel values by the constrast adjusting aplha
    img[:,:,0] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,0]]
    img[:,:,1] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,1]]
    img[:,:,2] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,2]]
    return responder()

#calling this module will convert alpha into the current contrast bar display
@app.route('/contrast_update', methods =['GET','POST'])
def contrast_update():
    #the contrast bar returns a number between 0 and 100 that represents the current level of contrast adjustment. 
    if alpha < 1.0:
        contrast_bar = (alpha - 0.5)*100
    else: 
        contrast_bar = alpha*50
    print alpha 
    print contrast_bar
    print type(contrast_bar)
    return str(contrast_bar)

#original contrast correcting code 
#img[:,:,2] = [[max(pixel - 25, 0) if pixel < 190 else min(pixel + 25, 255) for pixel in row] for row in img[:,:,2]]

@app.route('/click', methods =['GET','POST'])
def click():
    data = request.json
    cv.circle(img, (data['x']-8, data['y']-130), 3, (55, 255, 155), 3)
    return responder()

if __name__ == '__main__':
    app.run(debug=True, port=8080)