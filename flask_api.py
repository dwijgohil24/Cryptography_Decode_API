import math
import os
import hashlib
import logging
from flask import Flask, request, jsonify, send_file
import imutils
import numpy as np
import cv2
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# -------- Logging setup --------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def file_hash(path):
    """Return md5 hash of file to verify exact bytes"""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@app.route("/xor", methods=["POST"])
def xor_images():
    logger.info("==== XOR Endpoint Hit ====")

    # -------- Validate input --------
    if "image1" not in request.files or "image2" not in request.files:
        logger.error("Missing images in request")
        return jsonify({"error": "Both images are required"}), 400

    image1 = request.files["image1"]
    image2 = request.files["image2"]

    filename1 = secure_filename(image1.filename)
    filename2 = secure_filename(image2.filename)

    logger.info(f"Received filenames: {filename1}, {filename2}")

    path1 = os.path.join(UPLOAD_FOLDER, filename1)
    path2 = os.path.join(UPLOAD_FOLDER, filename2)

    image1.save(path1)
    image2.save(path2)

    # -------- File-level debugging --------
    size1 = os.path.getsize(path1)
    size2 = os.path.getsize(path2)

    logger.info(f"File sizes → image1: {size1} bytes, image2: {size2} bytes")
    logger.info(f"File hashes → image1: {file_hash(path1)}, image2: {file_hash(path2)}")

    # -------- Read images --------
    img1 = cv2.imread(path1, cv2.IMREAD_UNCHANGED)
    img2 = cv2.imread(path2, cv2.IMREAD_UNCHANGED)

    if img1 is None or img2 is None:
        logger.error("Failed to read one or both images")
        return jsonify({"error": "Invalid images"}), 400

    logger.info(f"IMG1 shape: {img1.shape}, dtype: {img1.dtype}")
    logger.info(f"IMG2 shape: {img2.shape}, dtype: {img2.dtype}")

    # -------- Shape check --------
    if img1.shape != img2.shape:
        logger.warning("Shape mismatch detected")
        return jsonify({"error": "Images must have the same dimensions"}), 400

    # -------- Rotation logic --------
    name = filename2.lower()
    logger.info(f"Checking rotation for filename: {name}")

    if "bmp2" in name:
        logger.info("Applying 90° rotation")
        img2 = cv2.rotate(img2, cv2.ROTATE_90_CLOCKWISE)
    elif "bmp3" in name:
        logger.info("Applying 180° rotation")
        img2 = cv2.rotate(img2, cv2.ROTATE_180)
    elif "bmp4" in name:
        logger.info("Applying 270° rotation")
        img2 = cv2.rotate(img2, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        logger.info("No rotation applied")

    logger.info(f"IMG2 shape after rotation: {img2.shape}")

    # -------- XOR --------
    try:
        xor_result = cv2.bitwise_xor(img1, img2)
        logger.info("XOR computation successful")
    except Exception as e:
        logger.error(f"XOR failed: {e}")
        return jsonify({"error": "XOR failed"}), 500

    # -------- Save result --------
    result_path = os.path.join(RESULT_FOLDER, "xor_result.bmp")
    cv2.imwrite(result_path, xor_result)

    logger.info(f"Result saved at: {result_path}")
    logger.info("==== XOR Completed ====")

    return send_file(result_path, mimetype="image/bmp")


if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 3000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
