from pymongo import MongoClient
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

URL = 'http://io_service:5000/save_session'

print("Authenthication server connected to database! :)")

@app.route("/save_session", methods=["POST"])
def register():
    req = request.json
    result = requests.post(url = URL, json = req)
    return Response(status=200)

if __name__ == '__main__':
    app.run(host="0.0.0.0")
