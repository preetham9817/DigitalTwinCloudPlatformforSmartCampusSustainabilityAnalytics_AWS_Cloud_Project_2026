from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return {
        "project": "Digital Twin Cloud Platform for Smart Campus Sustainability Analytics",
        "status": "Backend running"
    }

@app.route("/api/health")
def health():
    return {
        "status": "healthy"
    }

if __name__ == "__main__":
    app.run(debug=True)