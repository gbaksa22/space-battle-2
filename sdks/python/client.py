#!/usr/bin/python

import sys
import json
import random
import heapq

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
            data = self.rfile.readline().decode()  # reads until '\n' encountered
            json_data = json.loads(str(data))
            # uncomment the following line to see pretty-printed data
            # print(json.dumps(json_data, indent=4, sort_keys=True))
            response = game.get_command(json_data).encode()
            self.wfile.write(response)


class Game:
    def __init__(self):
        self.units = {}  # Dictionary to store unit details by unit ID
        self.directions = ['N', 'S', 'E', 'W']
        self.map = [[' ' for _ in range(10)] for _ in range(10)]  # Example 10x10 grid map for simplicity

    def get_command(self, json_data):
        # Update units and resources based on incoming JSON data
        self.update_units(json_data['unit_updates'])

        commands = []
        for unit_id, unit in self.units.items():
            if unit['type'] == 'worker':
                # Assign gathering task if resources are nearby
                command = self.worker_behavior(unit)
            elif unit['type'] == 'scout':
                # Assign exploration task for scouts
                command = self.scout_behavior(unit)
            elif unit['type'] == 'tank':
                # Basic tank behavior can be defensive or hold position
                command = self.tank_behavior(unit)
            
            if command:
                commands.append(command)
        
        response = json.dumps({"commands": commands}, separators=(',', ':')) + '\n'
        return response

    def update_units(self, unit_updates):
        # Update unit states based on the latest game data
        for unit in unit_updates:
            self.units[unit['id']] = {
                "type": unit['type'],
                "x": unit['x'],
                "y": unit['y'],
                "status": unit['status'],
                "resource": unit['resource'],
                "health": unit['health']
            }

    def a_star(self, start, goal):
        # A* implementation for grid-based movement
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # N, E, S, W

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                return self.reconstruct_path(came_from, current)

            for d in directions:
                neighbor = (current[0] + d[0], current[1] + d[1])
                if 0 <= neighbor[0] < len(self.map) and 0 <= neighbor[1] < len(self.map[0]) and self.map[neighbor[0]][neighbor[1]] != '#':
                    tentative_g_score = g_score[current] + 1

                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                        if neighbor not in [i[1] for i in open_set]:
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []  # Return an empty path if no path found

    def heuristic(self, a, b):
        # Manhattan distance heuristic
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def reconstruct_path(self, came_from, current):
        # Reconstruct path from goal to start
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def get_direction(self, current, next_node):
        # Convert coordinate difference to direction command
        dx = next_node[0] - current[0]
        dy = next_node[1] - current[1]
        if dx == -1 and dy == 0:
            return 'N'
        elif dx == 1 and dy == 0:
            return 'S'
        elif dx == 0 and dy == -1:
            return 'W'
        elif dx == 0 and dy == 1:
            return 'E'
        return None

    def worker_behavior(self, unit):
        goal = (5, 5)  # Example goal; you can set it dynamically based on resources
        start = (unit['x'], unit['y'])
        path = self.a_star(start, goal)

        if path:
            next_node = path[0]
            direction = self.get_direction(start, next_node)
            if direction:
                return {"command": "MOVE", "unit": unit['id'], "dir": direction}
        return None

    def scout_behavior(self, unit):
        goal = (0, 0)  # Example exploration goal; could dynamically change
        start = (unit['x'], unit['y'])
        path = self.a_star(start, goal)

        if path:
            next_node = path[0]
            direction = self.get_direction(start, next_node)
            if direction:
                return {"command": "MOVE", "unit": unit['id'], "dir": direction}
        return None

    def tank_behavior(self, unit):
        goal = (2, 2)  # Example defensive position
        start = (unit['x'], unit['y'])
        path = self.a_star(start, goal)

        if path:
            next_node = path[0]
            direction = self.get_direction(start, next_node)
            if direction:
                return {"command": "MOVE", "unit": unit['id'], "dir": direction}
        return None


if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '0.0.0.0'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
