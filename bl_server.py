from pymongo import MongoClient
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import os
import requests
import http
import json
import jwt
from functools import wraps
from math import sqrt

EMPTY = 0
WALL = 1
SHOP = 2
ENEMY = 3
PLAYER = 4
PLAYER_ON_SHOP = 5
PLAYER_ON_ENEMY = 6

PLAYER_TO_VACANT = {
    PLAYER : EMPTY,
    PLAYER_ON_SHOP : SHOP,
    PLAYER_ON_ENEMY : ENEMY
}

VACANT_TO_PLAYER = {
    EMPTY : PLAYER,
    SHOP : PLAYER_ON_SHOP,
    ENEMY : PLAYER_ON_ENEMY
}

STATE_IDLE = 0
STATE_SHOP = 1
STATE_FIGHT = 2

ATK_UPGRADE_COST = 5
SHIELD_UPGRADE_COST = 3
HEAL_COST = 2

app = Flask(__name__)
CORS(app)

JWT_SECRET = "secret"

IOSERVICE_URL = "http://io_service:5000/"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401

        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            uid = data["user_id"]
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users context to the routes
        return  f(uid, *args, **kwargs)

    return decorated

class GameState:

    STATE_TO_ACTION_TEXT = {
        STATE_IDLE : {
            1 : "up",
            2 : "down",
            3 : "left",
            4 : "right"
        },
        STATE_FIGHT : {
            1 : "flee up",
            2 : "flee down",
            3 : "flee left",
            4 : "flee right",
            5 : "attack",
            6 : "defend"
        },
        STATE_SHOP : {
            1 : "up",
            2 : "down",
            3 : "left",
            4 : "right",
            5 : f"upgrade atk ${ATK_UPGRADE_COST}",
            6 : f"upgrade shield ${SHIELD_UPGRADE_COST}",
            7:  f"heal ${HEAL_COST}"
        }
    }

    def __init__(self,
                 user_id,
                 health,
                 attack,
                 shield,
                 level,
                 game_map,
                 money,
                 scenario_id,
                 current_enemy_hp,
                 name,
                 blockTurns) -> None:
        self.user_id = user_id
        self.health = health
        self.attack = attack
        self.shield = shield
        self.level = level
        self.game_map = game_map
        self.money = money
        self.scenario_id = scenario_id
        self.current_enemy_hp = current_enemy_hp
        if PLAYER in game_map:
            self.state = STATE_IDLE
        elif PLAYER_ON_ENEMY in game_map:
            self.state = STATE_FIGHT
        elif PLAYER_ON_SHOP in game_map:
            self.state = STATE_SHOP
        self.action_text = GameState.STATE_TO_ACTION_TEXT[self.state]
        self.name = name
        self.blockTurns = blockTurns



    @staticmethod
    def fromJSON(data) -> 'GameState':
        return GameState(
            data.get('userID'),
            data.get('health'),
            data.get('attackPwr'),
            data.get('shield'),
            data.get('level'),
            data.get('map'),
            data.get('money'),
            data.get('scenarioID'),
            data.get('currentEnemyHP'),
            data.get('name'),
            data.get("blockTurnsRemaining")
        )

    def toJSON(self):
        return json.dumps(self.toDict())

    def toDict(self):
        return {
            "userID": self.user_id,
            "health" : self.health,
            "attackPwr" : self.attack,
            "shield" : self.shield,
            "level" : self.level,
            "money" : self.money,
            "map" : self.game_map,
            "scenarioID" : self.scenario_id,
            "currentEnemyHP" : self.current_enemy_hp,
            "rendered_map" : render(self.game_map),
            "name" : self.name,
            "blockTurnsRemaining" : self.blockTurns,
            "actions" : self.action_text
        }




@app.route("/act/<session_id>/<int:action_id>", methods=["POST"])
@token_required
def act(uid, session_id, action_id):

    result = requests.get(IOSERVICE_URL + "session/" + session_id)

    if (not result.ok):
        return Response(status=result.status_code)

    if result.json()["userID"] != uid:
        return Response(status=http.HTTPStatus.FORBIDDEN)

    game = GameState.fromJSON(result.json())

    if action_id <= 4:
        side = int(sqrt(len(game.game_map)))
        player_pos = game.game_map.index(PLAYER + game.state)
        player_x = player_pos // side
        player_y = player_pos % side

        move_delta = {
            1 : (-1,0),
            2 : (1,0),
            3 : (0,-1),
            4 : (0,1),
        }[action_id]

        new_x = player_x + move_delta[0]
        new_y = player_y + move_delta[1]
        new_pos = new_x * side + new_y

        if 0 <= new_x < side and 0 <= new_y < side and game.game_map[new_pos] != WALL:
            print(render(game.game_map), "\n\n")
            if game.game_map[new_pos] == ENEMY:
                game.current_enemy_hp = 50
            game.game_map[player_pos] = PLAYER_TO_VACANT[game.game_map[player_pos]]
            game.game_map[new_pos] = VACANT_TO_PLAYER[game.game_map[new_pos]]
            print(render(game.game_map), flush=True)

            requests.put(url=IOSERVICE_URL + "session/" + session_id, json=game.toDict())


            return Response(status=200, response=json.dumps("You walked"))
        else:
            return Response(status=200, response=json.dumps("You cannot walk there"))

    if game.state == STATE_SHOP:
        if action_id == 5:
            if game.money < ATK_UPGRADE_COST:
                return Response(status=200, response=json.dumps("You cannot afford that"))
            game.attack += 5
            game.money -= ATK_UPGRADE_COST
            requests.put(url=IOSERVICE_URL + "session/" + session_id, json=game.toDict())
            return Response(status=200, response=json.dumps("Your sword is sharper now"))
        if action_id == 6:
            if game.money < SHIELD_UPGRADE_COST:
                return Response(status=200, response=json.dumps("You cannot afford that"))
            game.shield += 4
            game.money -= SHIELD_UPGRADE_COST
            requests.put(url=IOSERVICE_URL + "session/" + session_id, json=game.toDict())
            return Response(status=200, response=json.dumps("Your shield is sturdier now"))
        if action_id == 7:
            if game.money < HEAL_COST:
                return Response(status=200, response=json.dumps("You cannot afford that"))
            if game.health == 100:
                return Response(status=200, response=json.dumps("You're already at full health!"))
            game.health = min(game.health + 5, 100)
            game.money -= HEAL_COST
            requests.put(url=IOSERVICE_URL + "session/" + session_id, json=game.toDict())
            return Response(status=200, response=json.dumps("You feel refreshed"))

    if game.state == STATE_FIGHT:

        ENEMY_ATTACK = {
            1 : 15,
            2 : 25,
            3 : 35
        }[game.level]


        if action_id == 5:
            # attack
            game.current_enemy_hp -= game.attack

            if game.current_enemy_hp > 0:
                # enemy attack

                blk_amount = game.shield

                if game.blockTurns > 0:
                    blk_amount += blk_amount // 2
                    game.blockTurns -= 1

                enemy_dmg = ENEMY_ATTACK - blk_amount

                if enemy_dmg > 0:
                    game.health -= enemy_dmg
                    if game.health <= 0:
                        # DEATH
                        # return and do something
                        requests.delete(url=IOSERVICE_URL + "session/" + session_id)
                        return Response(status=http.HTTPStatus.GONE, response="YOU DIED")
                    msg = f"the enemy attacked you for {enemy_dmg} damage"
                else:
                    msg = "you blocked the enemy's attack"
            else:
                # gain gold
                game.money += 15
                # remove enemy from map
                current_pos = game.game_map.index(PLAYER_ON_ENEMY)
                game.game_map[current_pos] = PLAYER
                msg = "the enemy died, giving you 15 gold"
            requests.put(url=IOSERVICE_URL + "session/" + session_id, json=game.toDict())
            return Response(status=200, response=json.dumps(msg))

        if action_id == 6:
            game.blockTurns = 3

            blk_amount = game.shield

            if game.blockTurns > 0:
                blk_amount += blk_amount // 2

            enemy_dmg = ENEMY_ATTACK - blk_amount

            if enemy_dmg > 0:
                game.health -= enemy_dmg
                if game.health <= 0:
                    # DEATH
                    requests.delete(url=IOSERVICE_URL + "session/" + session_id)
                    return Response(status=http.HTTPStatus.GONE, response="YOU DIED")
                msg = f"the enemy attacked you for {enemy_dmg} damage"
            else:
                msg = "you blocked the enemy's attack"
            requests.put(url=IOSERVICE_URL + "session/" + session_id, json=game.toDict())
            return Response(status=200, response=json.dumps(msg))

    return Response(status=http.HTTPStatus.NOT_IMPLEMENTED, response="you have no idea how to do that")


@app.route("/new_game", methods=["POST"])
@token_required
def newgame(uid):
    req = request.json
    if req is None:
        return Response(status=http.HTTPStatus.BAD_REQUEST)
    name = req["name"]
    level = req["level"]
    scenario = req["scenario"]

    STARTING_HEALTH = 100
    STARTING_ATTACK = 15
    STARTING_SHIELD = 15
    STARTING_MONEY = 0

    result = requests.post(IOSERVICE_URL + "session", json={
        "name": name,
        "userID": uid,
        "health" : STARTING_HEALTH,
        "attackPwr" : STARTING_ATTACK,
        "shield" : STARTING_SHIELD,
        "level" : level,
        "money" : STARTING_MONEY,
        "map" : generate_map(level),
        "scenarioID" : scenario,
        "currentEnemyHP" : 0,
        "blockTurnsRemaining" : 0
    })

    if not result.ok:
        return Response(status=result.status_code)

    return Response(status=http.HTTPStatus.CREATED, response=result.content)

@app.route("/saved_games", methods=["GET"])
@token_required
def savedgames(uid):
    result = requests.get(IOSERVICE_URL + uid + "/sessions")

    return Response(status=result.status_code, response=result.content)


@app.route("/session_data/<session_id>", methods=["GET"])
@token_required
def get_everything(uid, session_id):
    result = requests.get(IOSERVICE_URL + "session/" + session_id)

    if (not result.ok):
        return Response(status=result.status_code)

    game = GameState.fromJSON(result.json())

    if game.user_id != uid:
        return Response(status=http.HTTPStatus.FORBIDDEN)

    return Response(status=result.status_code, response=game.toJSON())

dungeon_side = {
    1 : 5,
    2 : 7,
    3 : 9
}

dungeon_enemies = {
    1 : 4,
    2 : 7,
    3 : 10
}


def generate_map(level, seed=None):
    side = dungeon_side[level]
    import random
    if seed is None:
        import time
        seed = time.time()
    rng = random.Random(seed)

    occupied = set()
    game_map = [[EMPTY for _ in range(side)] for _ in range(side)]

    def random_pos():
        pos = (rng.randrange(0, side), rng.randrange(0, side))
        while pos in occupied:
            pos = (rng.randrange(0, side), rng.randrange(0, side))
        return pos



    player_start_x, player_start_y = player_start = random_pos()
    game_map[player_start_x][player_start_y] = PLAYER
    occupied.add(player_start)

    shop_x, shop_y = shop = random_pos()
    game_map[shop_x][shop_y] = SHOP
    occupied.add(shop)

    objectives = {shop}

    for _ in range(dungeon_enemies[level]):
        enemy_x, enemy_y = enemy = random_pos()
        game_map[enemy_x][enemy_y] = ENEMY
        occupied.add(enemy)
        objectives.add(enemy)

    def wall_blocks(wall_pos):


        q = [player_start]
        vis = {player_start}

        def neigh(pos):
            x, y = pos
            potentials = set()
            if x >= 1:
                potentials.add((x-1,y))
            if x < side - 1:
                potentials.add((x+1,y))
            if y >= 1:
                potentials.add((x,y-1))
            if y < side - 1:
                potentials.add((x,y+1))
            return {t for t in potentials if t != wall_pos and game_map[t[0]][t[1]] != WALL and t not in vis}

        while q and objectives.difference(vis):
            np = q.pop()
            nei = neigh(np)
            q.extend(nei)
            vis.update(nei)

        return objectives.difference(vis)


    fails = 0
    fail_thresh = 5
    success = 0
    success_thresh = side * side / 2
    while fails < fail_thresh and success < success_thresh:
        wall_x, wall_y = wall = random_pos()
        if wall_blocks(wall):
            fails += 1
        else:
            success += 1
            occupied.add(wall)
            game_map[wall_x][wall_y] = WALL

    return [x for l in game_map for x in l]




def render(game_map, style=2):
    tile_to_char_1 = {
        EMPTY: " ",
        PLAYER: "P",
        WALL: "#",
        SHOP: "$",
        ENEMY: "E",
        PLAYER_ON_ENEMY: 'X',
        PLAYER_ON_SHOP: '€'
    }
    tile_to_char_2 = {
        EMPTY: " ",
        PLAYER: "P",
        WALL: "█",
        SHOP: "$",
        ENEMY: "E",
        PLAYER_ON_ENEMY: 'X',
        PLAYER_ON_SHOP: '€'
    }

    ml = []

    n = int(sqrt(len(game_map)))

    while game_map:
        ml.append(game_map[:n])
        game_map = game_map[n:]

    if style == 1:
        ms = ["┌" + (n * 2 + 1) * "─" + "┐", *["│ " + " ".join([tile_to_char_1[t] for t in r]) + " │" for r in ml],"└" + (n * 2 + 1) * "─" + "┘"]
        s = "\n".join(ms)
    else:
        ms = ["█" + (n * 2 + 1) * "█" + "█", *["█ " + " ".join([tile_to_char_2[t] for t in r]) + " █" for r in ml],"█" + (n * 2 + 1) * "█" + "█"]

        s = "\n".join(ms).replace("█ █", "███").replace("█ █", "███")

    return s





if __name__ == '__main__':
    app.run(host="0.0.0.0")
