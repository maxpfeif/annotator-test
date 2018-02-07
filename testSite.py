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

#standard image load informtion
img_path = 'volvoExample.png' #sample image path
img = cv.imread(img_path)
disp_W = 600 #width to size displayed images to 
disp_H = 330 #height to size displayed images to 
img = cv.resize(img, (disp_W, disp_H))

#zoom control variables 
img_adj = img #image reference for keeping track of zoom and pan adjustments
zoom = 1 #keeps track of our zoom power
zoom_step = 1.5
dX = disp_W/2 #delta x, used for keeping track of zoom center
dY = disp_H/2 # delta y, used for keeping track of zoom center

app = Flask(__name__)

#initialize the HTML page upon launching the script. 
@app.route('/')
def index():
    return render_template('index.html')

#method that returns the state to the client, has some parent dependencies. 
def responder(content, item):
    retval, buffer = cv.imencode('.jpg', item)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = content # default to 'image/jpg'
    return response  

#Primary Zoom Execution method. 
#   Takes a boolean "zoom" which is true if in, false if out.
#   Needs a center position to zoom at, X and Y.  
#   Returns the result, as a new image, resized to global standard. 
def zoomer(x, y, zoom):
    global img_adj, dX, dY
    if(zoom == 1):
        #reset the center delta positions
        dX = disp_W/2 
        dY = disp_H/2 
        return img 
    else:
        #calculate new imag_adj width rel to img
        zoom_W = disp_W/int((zoom_step**zoom))
        zoom_H = disp_H/int((zoom_step**zoom))
        #caldule the new dX and dY
        dX += (x - dX)
        dY += (y - dY)
        #need to make sure we aren't going to push off of the edge
        if((dX + zoom_W/2) > disp_W):
            dX = disp_W - zoom_W/2
        if((dX - zoom_W/2) < 0):
            dX = zoom_W/2
        if((dY + zoom_H/2) > disp_H):
            dY = disp_H - zoom_H/2 
        if((dY - zoom_H/2) < 0):
            dY = zoom_H/2
        #define X1, X2, Y1, Y2 from zoom and modified center point
        X1 = dX-(zoom_W/2)
        Y1 = dY-(zoom_H/2)
        X2 = dX+(zoom_W/2)
        Y2 = dY+(zoom_H/2)
        #need to check edge cases 
        if(X1 < 0):
            X1 = 0
        if(Y1 < 0):
            Y1 = 0
        if(X2 > disp_W):
            X2 = disp_W
        if(Y2 > disp_H):
            Y2 = disp_H
        #now generate clipped region 
        img_adj = img[Y1:Y2, X1:X2]
        img_adj = cv.resize(img_adj, (disp_W, disp_H), 0,0,1)
        return img_adj  

#intial and original image update module 
@app.route('/image', methods = ['GET', 'POST'])
def image():
    global img, img_adj, alpha, zoom 
    #reset the contrast and zoom when returning to original state
    alpha = 1.0 
    zoom = 1
    img_adj = img
    img = cv.imread(img_path)
    img = cv.resize(img, (disp_W, disp_H))
    if request.method == "POST":
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
        cv.threshold(img, 140, 255, 0, img) 
    return responder('image/jpg', img)


@app.route('/zoom_ctrl', methods =['GET','POST'])
def zoom_ctrl():
    global img, img_adj, zoom 
    #get the zoom adjustment specs from the client
    img_adjust = request.json
    x = int(img_adjust['x'])
    y = int(img_adjust['y'])
    dz = int(img_adjust['dz'])
    if (dz > 0 and (zoom < 4)): 
        zoom += 1 
        img_adj = zoomer(x,y, zoom)   
    if (dz < 0 and zoom > 1):
        zoom -= 1
        img_adj = zoomer(x,y, zoom)   
    return responder('image/jpg', img_adj)

@app.route('/pan_ctrl', methods =['GET','POST'])
def pan_ctrl():
    global img_adj, dX, dY
    pan_delta = request.json
    if(pan_delta['kC'] == 38):
        dY -= 10
    if(pan_delta['kC'] == 40):
        dY += 10
    if(pan_delta['kC'] == 37):
        dX -= 10
    if(pan_delta['kC'] == 39):
        dX += 10
    img_adj = zoomer(dX, dY, zoom)
    return responder('image/jpg', img_adj)

#simple method for processing edge detection. 
@app.route('/egde')
def edge():
    global img
    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    img = cv.Canny(img,50,150)
    #makes sure the zoom is reflective of current state with edges on
    img = zoomer()
    return responder('image/jpg', img)

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
    return responder('image/jpg', img)
   
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
    return responder('image/jpg', img)

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

if __name__ == '__main__':
    app.run(debug=True, port=8080)