from pymongo import MongoClient
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import os
import requests
import http
import json

app = Flask(__name__)
CORS(app)


@app.route("/act/<session_id>", methods=["POST"])
def act(session_id):
    action = request.json
    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=f"This will be the response you get after the action {action} for {session_id=}")

@app.route("/player_stats/<session_id>", methods=["GET"])
def stats(session_id):
    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=json.dumps({"health":100, "attack":50, "shield": 20, "gold": 67}))

@app.route("/map/<session_id>", methods=["GET"])
def map(session_id):
#   e # _ _ $
#   _ # e _ _
#   _ _ P _ _
#   _ _ # # #
#   _ _ _ e _

    EMPTY = 0
    PLAYER = 1
    WALL = 2
    SHOP = 3
    ENEMY = 4


    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=json.dumps(
        [
            ENEMY,  WALL,   EMPTY,  EMPTY,  SHOP,
            EMPTY,  WALL,   ENEMY,  EMPTY,  EMPTY,
            EMPTY,  EMPTY,  PLAYER, EMPTY,  EMPTY,
            EMPTY,  EMPTY,  WALL,   WALL,   WALL,
            EMPTY,  EMPTY,  EMPTY,  ENEMY,  EMPTY
        ]
    ))

@app.route("/scenario/<session_id>", methods=["GET"])
def scenario(session_id):
    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=json.dumps(f"This will be the scenario description for {session_id=}"))

@app.route("/actions/<session_id>", methods=["GET"])
def actions(session_id):
    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=json.dumps({1: "up", 2: "down", 3: "left", 4: "right"}))

@app.route("/new_game/<user_id>", methods=["GET"]) # TODO decide if get is the best method
def newgame(user_id):
    req = request.json
    name = req["name"]
    level = req["level"]
    scenario = req["scenario"]
    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=json.dumps(f"id of the new game named {name} of level {level} on scenario {scenario}"))

@app.route("/saved_games/<user_id>", methods=["GET"])
def savedgames(user_id):
    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=json.dumps(["name1", "name2", "etc..."]))

@app.route("/load_game/<user_id>/<game_name>", methods=["GET"]) # TODO decide if get is the best method
def loadgame(user_id, game_name):
    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response=json.dumps("id of the session"))

if __name__ == '__main__':
    app.run(host="0.0.0.0")
