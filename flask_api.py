import os
import hashlib
import logging
import imutils
from flask import Flask, request, jsonify, send_file
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

    # -------- File debugging --------
    logger.info(f"File sizes → {os.path.getsize(path1)}, {os.path.getsize(path2)}")
    logger.info(f"Hashes → {file_hash(path1)}, {file_hash(path2)}")

    # -------- Read images --------
    img1 = cv2.imread(path1, cv2.IMREAD_UNCHANGED)
    img2 = cv2.imread(path2, cv2.IMREAD_UNCHANGED)

    if img1 is None or img2 is None:
        logger.error("Failed to read images")
        return jsonify({"error": "Invalid images"}), 400

    logger.info(f"IMG1 shape: {img1.shape}")
    logger.info(f"IMG2 shape: {img2.shape}")

    # -------- 🔥 CRITICAL FIX: normalize channels --------
    # Convert RGBA → BGR if needed
    if len(img1.shape) == 3 and img1.shape[2] == 4:
        logger.info("Converting IMG1 from 4-channel to 3-channel")
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGRA2BGR)

    if len(img2.shape) == 3 and img2.shape[2] == 4:
        logger.info("Converting IMG2 from 4-channel to 3-channel")
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGRA2BGR)

    logger.info(f"After normalization → IMG1: {img1.shape}, IMG2: {img2.shape}")

    # -------- Rotation --------
    name = filename2.lower()
    
    if "bmp2" in name:
        logger.info("Applying 90° rotation (imutils)")
        img2 = imutils.rotate(img2, 90)
    
    elif "bmp3" in name:
        logger.info("Applying 180° rotation (imutils)")
        img2 = imutils.rotate(img2, 180)
    
    elif "bmp4" in name:
        logger.info("Applying 270° rotation (imutils)")
        img2 = imutils.rotate(img2, 270)
    
    else:
        logger.info("No rotation applied")

    # -------- Ensure same dimensions AFTER rotation --------
    if img1.shape != img2.shape:
        logger.warning("Resizing img2 to match img1")
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # -------- XOR --------
    try:
        xor_result = cv2.bitwise_xor(img1, img2)
        logger.info("XOR successful")
    except Exception as e:
        logger.error(f"XOR failed: {e}")
        return jsonify({"error": "XOR failed"}), 500

    # -------- Save result --------
    result_path = os.path.join(RESULT_FOLDER, "xor_result.bmp")
    cv2.imwrite(result_path, xor_result)

    logger.info("==== XOR Completed ====")

    return send_file(result_path, mimetype="image/bmp")


if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 3000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
