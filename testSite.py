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

alpha = 1.0 #simple brightness control, ranges from 0.5 to 2.5 in 0.1 steps.
app = Flask(__name__)


@app.route('/image', methods = ['GET', 'POST'])
def image():
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    if request.method == "POST":
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
        cv.threshold(img, 140, 255, 0, img)
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    #reset the contrast when returning to original state
    global alpha     
    alpha = 1.0 
    return response

@app.route('/')
def index():
    return render_template('index.html')

#@app.route('/test', methods = ['GET', 'POST'])
#def test():
#    img_path = 'sample.jpg'
#    img = cv.imread(img_path)
#    img = cv.resize(img, (320, 240))
#    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
#    cv.threshold(img, 140, 255, 0, img)
#    retval, buffer = cv.imencode('.jpg', img)
#    response = make_response(buffer.tobytes())
#    response.headers['Content-Type'] = 'image/jpg'
#    return response

@app.route('/egde')
def edge():
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    img = cv.Canny(img,50,150)
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response

#this module incriments the contrast
@app.route('/contrast_plus')
def contrast_plus():
    global alpha 
    if alpha < 2.0:
        alpha += 0.1
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    #iterate through the pixels and multiply the individual pixel values by the constrast adjusting aplha
    img[:,:,0] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,0]]
    img[:,:,1] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,1]]
    img[:,:,2] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,2]]
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response
   
#this module decriments the image contrast 
@app.route('/contrast_minus')
def contrast_minus():
    global alpha
    if alpha > 0.5:
        alpha -= 0.1
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    #iterate through the pixels and multiply the individual pixel values by the constrast adjusting aplha
    img[:,:,0] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,0]]
    img[:,:,1] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,1]]
    img[:,:,2] = [[max(pixel*alpha, 0) if pixel*alpha < 256 else min(pixel*alpha, 255) for pixel in row] for row in img[:,:,2]]
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response

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
    img_path = 'sample.jpg'
    data = request.json
    print(data)
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    cv.circle(img, (data['x']-8, data['y']-130), 3, (55, 255, 155), 3)
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response

if __name__ == '__main__':
    app.run(debug=True, port=8080)