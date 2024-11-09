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
            response = game.get_command(json_data).encode()
            self.wfile.write(response)

class Game:
    def __init__(self):
        self.units = set()  # Set of unique unit IDs
        self.unit_info = {}  # Dictionary to store unit details by ID
        self.directions = ['N', 'S', 'E', 'W']
        self.map = []  # 2D array for the game map
        self.width = 0
        self.height = 0
        self.player_id = None


    def initialize_map(self, game_info):
        self.width = game_info['map_width']
        self.height = game_info['map_height']
        # Creates a 2D array filled with '?'
        self.map = [['?' for _ in range(2 * self.width + 1)] for _ in range(2 * self.height + 1)]

    def update_map(self, json_data):
    # Process tile updates
        if 'tile_updates' in json_data:
            tile_updates = json_data['tile_updates']
            for tile in tile_updates:
                if tile['visible']:
                    x, y = tile['x'], tile['y']
                    if tile['resources']:
                        resource = tile['resources']
                        print(f"Resource found at ({x}, {y}): Type = {resource['type']}, Total = {resource['total']}, Value per load = {resource['value']}")
                        self.map[y][x] = 'r'  # Mark tile with 'r' for resources
                        print(f'resource at {x}, {y}')
                    elif tile['blocked']:
                        self.map[y][x] = '#'
                        print(f'wall at {x}, {y}')
                    elif tile['units']:
                        self.map[y][x] = 'E'  # Enemy unit
                    else:
                        self.map[y][x] = ' '  # Empty tile

        # Process unit updates
        if 'unit_updates' in json_data:
            for unit in json_data['unit_updates']:
                unit_id = unit['id']
                self.units.add(unit_id)  # Store ID in set
                self.unit_info[unit_id] = unit  # Store full info in dictionary


    def get_map(self):
        return self.map
    
    def print_map(self):
        print("Current Map:")
        for row in self.map:
            print(''.join(row))
        print()  # Extra newline for readability

    def get_command(self, json_data):
        # Initialize map on the first turn if necessary
        if 'game_info' in json_data and not self.map:
            self.initialize_map(json_data['game_info'])
            self.player_id = json_data['player']

        # Update the map with new tile and unit data each turn
        self.update_map(json_data)
        
        # Print the updated map
        #self.print_map()

        # Generate commands for units
        commands = []
        for unit_id in self.units:
            unit = self.unit_info[unit_id]
            if unit['type'] == 'worker':  # Example condition
                command = {"command": "MOVE", "unit": unit_id, "dir": "S"}
                commands.append(command)

        return json.dumps({"commands": commands}, separators=(',', ':')) + '\n'


if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '0.0.0.0'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
