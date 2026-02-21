from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import detector
import os

app = Flask(__name__)
CORS(app)

# Load YOLO Model (Mock or Real)
# model = YOLO("yolov8n.pt") 
# For this environment, we will use a robust mock/simulation if weights aren't found
# or we can try to download them.

@app.route('/')
def home():
    return "SafeDrive AI Engine Running 📸"

@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # Perform Detection
    results = detector.detect_objects(img)
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
