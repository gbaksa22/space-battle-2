#!/usr/bin/python

import sys
import json
import random

if (sys.version_info > (3, 0)):
    print("Python 3.X detected")
    import socketserver as ss
else:
    print("Python 2.X detected")
    import SocketServer as ss


class NetworkHandler(ss.StreamRequestHandler):
    def handle(self):
        game = Game()

        while True:
            data = self.rfile.readline().decode() # reads until '\n' encountered
            json_data = json.loads(str(data))
            # uncomment the following line to see pretty-printed data
            # print(json.dumps(json_data, indent=4, sort_keys=True))
            response = game.get_random_move(json_data).encode()
            self.wfile.write(response)



class Game:
    def __init__(self):
        self.units = set() # set of unique unit ids
        self.directions = ['N', 'S', 'E', 'W']
        self.map = []  # 2D array for the game map
        self.width = 0
        self.height = 0
        self.player_id = None
        #self.map = [[' ' for _ in range(10)] for _ in range(10)]  # Example 10x10 grid map for simplicity

    def initialize_map(self, game_info):
        self.width = game_info['map_width']
        self.height = game_info['map_height']
        # Creates a 2D array filled with '?'
        self.map = [['?' for _ in range(2 * self.width + 1)] for _ in range(2 * self.height + 1)]

    def update_map(self, tile_updates, unit_updates):
        # Update map based on tile updates
        for tile in tile_updates:
            x, y = tile['x'], tile['y']
            if tile['blocked']:
                self.map[y][x] = '#'
            elif tile['resources']:
                self.map[y][x] = 'R'
            elif tile['units']:
                self.map[y][x] = 'E'
            else:
                self.map[y][x] = ' '

        # Update map based on unit updates
        for unit in unit_updates:
            x, y = unit['x'], unit['y']
            if unit['type'] == 'base' and unit['player_id'] == self.player_id:
                self.map[y][x] = 'B'
            elif unit['player_id'] != self.player_id:
                self.map[y][x] = 'E'

    def get_map(self):
        return self.map

    def get_random_move(self, json_data):
        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])
        self.units |= units # add any additional ids we encounter
        unit = random.choice(tuple(self.units))
        direction = random.choice(self.directions)
        move = 'MOVE'
        command = {"commands": [{"command": move, "unit": unit, "dir": direction}]}
        response = json.dumps(command, separators=(',',':')) + '\n'
        return response

if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '0.0.0.0'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
