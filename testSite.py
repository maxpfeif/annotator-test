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



app = Flask(__name__)


@app.route('/image', methods = ['GET', 'POST'])
def image():
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    if request.method == "POST":
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
        cv.threshold(img, 140, 255, 0, img)
        print("herhe")
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/test', methods = ['GET', 'POST'])
def test():
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    cv.threshold(img, 140, 255, 0, img)
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response



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

#method for adjusting the color 
@app.route('/contrast')
def contrast():
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    img[:,:,2] = [[max(pixel - 25, 0) if pixel < 190 else min(pixel + 25, 255) for pixel in row] for row in img[:,:,2]]
    retval, buffer = cv.imencode('.jpg', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpg'
    return response

#method that adjusts the contrast based on the contrast variable 
@app.route('/cont_plus', methods = ['GET','POST'])
def cont_plus():
    gamma = 1.5
    img_path = 'sample.jpg'
    img = cv.imread(img_path)
    img = cv.resize(img, (320, 240))
    
    img = cv.cvtColor(img, cv.COLOR_BGR2LAB) 
    l, a, b = cv.split(img)
    clahe = cv.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
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