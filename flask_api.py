import math
from flask import Flask, request, jsonify, send_file
import imutils
import numpy as np
import cv2
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route("/xor", methods=["POST"])
def xor_images():
    print("XOR Endpoint")
    if "image1" not in request.files or "image2" not in request.files:
        return jsonify({"error": "Both images are required"}), 400
    
    image1 = request.files["image1"]
    image2 = request.files["image2"]
    
    filename1 = secure_filename(image1.filename)
    filename2 = secure_filename(image2.filename)
    path1 = os.path.join(UPLOAD_FOLDER, filename1)
    path2 = os.path.join(UPLOAD_FOLDER, filename2)
    
    image1.save(path1)
    image2.save(path2)
    
    img1 = cv2.imread(path1, cv2.IMREAD_UNCHANGED)
    img2 = cv2.imread(path2, cv2.IMREAD_UNCHANGED)
    
    if img1.shape != img2.shape:
        return jsonify({"error": "Images must have the same dimensions"}), 400
    
    if filename2.lower() == "bmp2.bmp":
        degrees = math.degrees(1.57079632)
        img2 = imutils.rotate(img2, degrees)
    elif filename2.lower() == "bmp3.bmp":
        degrees = math.degrees(3.14159265)
        img2 = imutils.rotate(img2, degrees)
    elif filename2.lower() == "bmp4.bmp":
        degrees = math.degrees(4.71238898)
        img2 = imutils.rotate(img2, degrees)        
            
    xor_result = cv2.bitwise_xor(img1, img2)
    result_path = os.path.join(RESULT_FOLDER, "xor_result.bmp")
    cv2.imwrite(result_path, xor_result)
    
    return send_file(result_path, mimetype="image/bmp")

if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 3000))
    app.run(host="0.0.0.0", debug=False, port=port)
