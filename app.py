from flask import Flask, jsonify, render_template, request
from utils.utils import parse_whatsapp_export, compute_stats


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    uploaded = request.files["file"]
    
    if not uploaded or uploaded.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        text = uploaded.stream.read().decode("utf-8", errors="ignore")
    except Exception:
        return jsonify({"error": "Failed to read file"}), 400

    messages = parse_whatsapp_export(text)
    data = compute_stats(messages)
    
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)


