from flask import Flask
from flask import render_template
from flask import make_response
from flask import request
import cv2 as cv
import json
import numpy as np
# enables display of detailed error reports for debugging. Remove this when the program is ready for launch
import cgitb
cgitb.enable()

# ----------------------------------------------------------*
# ---------------------GLOBAL VARIABLES---------------------*
# ----------------------------------------------------------*

# contrast control variable
alpha = 1 # simple brightness control, ranges from 0.5 to 2.5 in 0.1 steps.
alpha_min = 1   
alpha_max = 5
alpha_range = int(alpha_max - alpha_min)*10

# edge detection boolean
edges = False 
# zoom control variables
disp_W = 600  # width to size displayed images to
disp_H = 330  # height to size displayed images to
zoom = 1  # keeps track of our zoom power
zoom_step = 1.5
dX = disp_W/2  # delta x, used for keeping track of zoom center
dY = disp_H/2  # delta y, used for keeping track of zoom center
# standard image load information
img_path = 'nightExample.jpg'  # sample image path
# the img object stores the original image, with any contrast of filters made to it
img = cv.imread(img_path)
img = cv.resize(img, (disp_W, disp_H))
# keep an original copy without reading from the file
img_org = img
# image reference for keeping track of zoom display
img_adj = img  
# create CLAHE object for contrast adjustment
clahe = cv.createCLAHE()
# clipLimit=2.0, tileGridSize=(8,8) args for CLAHE creation

# img_alpha={}
# for x in range(1,alpha_range):
#    global img
#    iterate through the alpha values and create images for each possible contrast setting
#    img_alpha[(x)[:,:,0]] = [[max(pixel*alpha, 0)
#    if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,0]]
#    img_alpha["{0}".format(x)[:,:,1]] = [[max(pixel*alpha, 0)
#    if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,1]]
#    img_alpha["{0}".format(x)[:,:,2]]= [[max(pixel*alpha, 0)
#    if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,2]]


app = Flask(__name__)


# initialize the HTML page upon launching the script. 
@app.route('/')
def index():
    return render_template('index.html')


# method that returns the state to the client, has some parent dependencies. 
def responder(content, item):
    retval, buffer = cv.imencode('.jpg', item)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = content  # default to 'image/jpg'
    return response  


# Primary Zoom Execution method.
#   Takes a boolean "zoom" which is true if in, false if out.
#   Needs a center position to zoom at, X and Y.  
#   Returns the result, as a new image, resized to global standard. 
def zoomer(x, y, zoom):
    global img_adj, dX, dY
    if(zoom == 1):
        # reset the center delta positions
        dX = disp_W/2 
        dY = disp_H/2 
        return img 
    else:
        # calculate new imag_adj width rel to img
        zoom_W = disp_W/int((zoom_step**zoom))
        zoom_H = disp_H/int((zoom_step**zoom))
        # caldule the new dX and dY
        dX += (x - dX)
        dY += (y - dY)
        # need to make sure we aren't going to push off of the edge
        if dX + zoom_W/2 > disp_W:
            dX = disp_W - zoom_W/2
        if dX - zoom_W/2 < 0:
            dX = zoom_W/2
        if dY + zoom_H/2 > disp_H:
            dY = disp_H - zoom_H/2 
        if dY - zoom_H/2 < 0:
            dY = zoom_H/2
        # define X1, X2, Y1, Y2 from zoom and modified center point
        X1 = int(dX-(zoom_W/2))
        Y1 = int(dY-(zoom_H/2))
        X2 = int(dX+(zoom_W/2))
        Y2 = int(dY+(zoom_H/2))
        # need to check edge cases 
        if X1 < 0:
            X1 = 0
        if Y1 < 0:
            Y1 = 0
        if X2 > disp_W:
            X2 = disp_W
        if Y2 > disp_H:
            Y2 = disp_H
        #  generate clipped region
        print(Y1, Y2, X1, X2)
        img_adj = img[Y1:Y2, X1:X2]
        img_adj = cv.resize(img_adj, (disp_W, disp_H), 0,0,1)
        return img_adj  

# initial and original image update module
@app.route('/image', methods=['GET', 'POST'])
def image():
    global img, alpha, zoom, dX, dY, edges 
    # reset the contrast and zoom when returning to original state
    alpha = 1
    zoom = 1
    edges = False
    dX = disp_W/2 
    dY = disp_H/2
    img = cv.imread(img_path)
    img = cv.resize(img, (disp_W, disp_H))
    if request.method == "POST":
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
        cv.threshold(img, 140, 255, 0, img) 
    return responder('image/jpg', img)


@app.route('/zoom_ctrl', methods=['GET', 'POST'])
def zoom_ctrl():
    global img, img_adj, zoom 
    # get the zoom adjustment specs from the client
    img_adjust = request.json
    x = int(img_adjust['x'])
    y = int(img_adjust['y'])
    dz = int(img_adjust['dz'])
    if dz > 0 and (zoom < 4):
        zoom += 1 
        img_adj = zoomer(x, y, zoom)
    if dz < 0 and zoom > 1:
        zoom -= 1
        img_adj = zoomer(x, y, zoom)
    return responder('image/jpg', img_adj)

@app.route('/pan_ctrl', methods=['GET', 'POST'])
def pan_ctrl():
    global img_adj, dX, dY
    pan_delta = request.json
    if pan_delta['kC'] == 38:
        dY -= 10
    if pan_delta['kC'] == 40:
        dY += 10
    if pan_delta['kC'] == 37:
        dX -= 10
    if pan_delta['kC'] == 39:
        dX += 10
    img_adj = zoomer(dX, dY, zoom)
    return responder('image/jpg', img_adj)


# simple method for processing edge detection. 
@app.route('/egde')
def edge():
    global img, edges 
    if edges:
        edges = False
        img = cv.imread(img_path)
        img = cv.resize(img, (disp_W, disp_H))
        img = contraster()        
    else: 
        edges = True
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
        img = cv.Canny(img,50,150)
    # makes sure the zoom is reflective of current state with edges on
    img_adj = zoomer(dX, dY, zoom)
    return responder('image/jpg', img_adj)


# this module incriments the contrast
@app.route('/contrast_plus')
def contrast_plus():
    global alpha, img 
    clahe = cv.createCLAHE(clipLimit=1.5, tileGridSize=(1,1))
    if alpha < alpha_max:
        alpha += 1
        lab = cv.cvtColor(img, cv.COLOR_BGR2LAB)
        l, a, b = cv.split(lab)
        cl = clahe.apply(l)
        limg = cv.merge((cl,a,b))    
        img = cv.cvtColor(limg, cv.COLOR_LAB2BGR)
    img_adj = zoomer(dX, dY, zoom)
    return responder('image/jpg', img_adj)
 
   
# this module decriments the image contrast 
@app.route('/contrast_minus')
def contrast_minus():
    global alpha, img, img_adj
    clahe = cv.createCLAHE(clipLimit=1.5, tileGridSize=(1,1))
    if alpha > 1:
        alpha -= 1
        img = img_org 
        for i in range(1,int(alpha)):
            lab = cv.cvtColor(img, cv.COLOR_BGR2LAB)
            l, a, b = cv.split(lab)
            cl = clahe.apply(l)
            lab = cv.merge((cl,a,b))    
            img = cv.cvtColor(lab, cv.COLOR_LAB2BGR)
    img_adj = zoomer(dX, dY, zoom)
    return responder('image/jpg', img_adj)


# calling this module will convert alpha into the current contrast bar display
@app.route('/contrast_update', methods =['GET','POST'])
def contrast_update():
    # the contrast bar returns a number between 0 and 100 that represents the current level of contrast adjustment.
    if alpha < 1:
        contrast_bar = (alpha - 0.5)*100
    else: 
        contrast_bar = alpha*50
    return str(contrast_bar)

# using this to get the rect info and append to a json file
# TODO: update this interface to support line json format
@app.route('/click', methods =['GET','POST'])
def click():
    global img
    data = request.json
    # check your json file
    print(data)
    # TODO: this mechanism may be time consuming and memory consuming. Can we directly append to the json?
    # read in previous json file
    with open('data.json', 'r') as outfile:
        print(outfile)
        try:
            previous = json.load(outfile)
        except:
            previous = {}
        if data['type'] == 'box':
            if 'raw_file' not in previous:
                previous['raw_file'] = img_path
            if 'Labels' not in previous:
                previous['Labels'] = []
            if 'Positions' not in previous:
                previous['Positions'] = []
            previous['Labels'].append(data['catagrey'])
            previous['Positions'].append([data['x'], data['y'], data['w'], data['h']])
        if data['type'] == 'line':
            if 'raw_file' not in previous:
                previous['raw_file'] = img_path
            if 'labels' not in previous:
                previous['labels'] = []
            if 'h_samples' not in previous:
                previous['h_samples'] = []
            if 'lanes' not in previous:
                previous['lanes'] = []
            previous['Labels'].append(data['catagrey'])

    with open('data.json', 'w') as outfile:
        json.dump(previous, outfile)
    img_adj = img
    if data['type'] == 'line':
        coordinate = []
        for i in range(len(data['list'])):
            point = []
            point.append(data['list'][i]['x'])
            point.append(data['list'][i]['y'])
            coordinate.append(point)
        print(coordinate)
        print(data['catagrey'])
        points = np.array(coordinate)
        cv.polylines(img_adj, np.int32([points]), False, (255, 0, 0), 1)
    else:
        cv.rectangle(img_adj, (data['x'], data['y']), (data['x'] + data['w'], data['y'] + data['h']), (0, 255, 0), 3)

    return responder('image/jpg', img_adj)


if __name__ == '__main__':
    app.run(debug=True, port=8000)
