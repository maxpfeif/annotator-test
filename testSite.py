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

alpha = 1.0 #simple brightness control
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

#
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

#original contrast correcting code 
#img[:,:,2] = [[max(pixel - 25, 0) if pixel < 190 else min(pixel + 25, 255) for pixel in row] for row in img[:,:,2]]

#method that adjusts the contrast based on the contrast variable 
@app.route('/cont_plus', methods = ['GET','POST'])
def cont_plus():
    gamma = 1.5
    inv_gamma = 1/gamma
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    #convert the color profile to LAB 
    img = cv.cvtColor(img, cv.COLOR_BGR2LAB) 
    #split the channels into Lightness, a (green to magenta) and b (blue to yellow)
    l, a, b = cv.split(img)
    #use CLAHE process 
    # clahe = cv.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    # cl = clahe.apply(l)
    #try just adjusting the 'lightness' only
    #cl = l / np.uint(gamma)
    #re-merge the results
    img = cv.merge((cl,a,b))
    img = cv.cvtColor(img, cv.COLOR_LAB2BGR)

    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response


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