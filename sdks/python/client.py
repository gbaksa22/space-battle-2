#!/usr/bin/python

from collections import deque
import heapq
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
        # Initialize map and player_id if necessary
        if 'game_info' in json_data and not self.map:
            self.initialize_map(json_data['game_info'])
            self.player_id = json_data['player']
            self.unit_directions = {}  # Store each worker's current direction

        # Update map with new tile and unit data each turn
        self.update_map(json_data)

        # Define initial directions for each new worker
        initial_directions = ['N', 'E', 'S', 'W']
        direction_map = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
        commands = []

        for unit_id in self.units:
            unit = self.unit_info[unit_id]
            start = (unit['x'], unit['y'])

            if unit['type'] == 'worker':
                # Assign initial direction to each worker if not set
                if unit_id not in self.unit_directions:
                    self.unit_directions[unit_id] = initial_directions[len(self.unit_directions) % 4]

                if unit['resource'] > 0:  # Worker is carrying a resource
                    # Find path back to base using A*
                    path = self.a_star_find_path(start, target='b')
                    if path:
                        next_position = path[0]
                        direction = self.get_direction(start, next_position)
                        command = {"command": "MOVE", "unit": unit_id, "dir": direction}
                    else:
                        random_direction = random.choice(self.directions)
                        command = {"command": "MOVE", "unit": unit_id, "dir": random_direction}

                else:  # Worker is not carrying a resource
                    # Find the nearest resource with BFS
                    path = None
                    if path:
                        # If path to resource found, move towards it
                        next_position = path[0]
                        direction = self.get_direction(start, next_position)
                        if len(path) == 1:
                            command = {"command": "GATHER", "unit": unit_id, "dir": direction}
                        else:
                            command = {"command": "MOVE", "unit": unit_id, "dir": direction}
                    else:
                        # Continue in the assigned direction until blocked
                        current_direction = self.unit_directions[unit_id]
                        dx, dy = direction_map[current_direction]
                        next_position = (start[0] + dx, start[1] + dy)

                        # Check if the next tile is within bounds and not a wall
                        if self.is_within_bounds(next_position) and self.map[next_position[1]][next_position[0]] != '#':
                            command = {"command": "MOVE", "unit": unit_id, "dir": current_direction}
                        else:
                            # Change direction clockwise if a wall is hit
                            new_direction_index = (initial_directions.index(current_direction) + 1) % 4
                            new_direction = initial_directions[new_direction_index]
                            self.unit_directions[unit_id] = new_direction
                            command = {"command": "MOVE", "unit": unit_id, "dir": new_direction}

                commands.append(command)

        return json.dumps({"commands": commands}, separators=(',', ':')) + '\n'




    def a_star_find_path(self, start, target='b'):
        """
        A* search to find the shortest path to the nearest target tile (e.g., 'b' for base).
        Returns a list of coordinates to reach the target tile.
        """
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, target_tile=target)}

        directions = {
            (0, -1): 'N',
            (0, 1): 'S',
            (-1, 0): 'W',
            (1, 0): 'E'
        }

        while open_set:
            _, current = heapq.heappop(open_set)

            # If we have reached the base tile, reconstruct the path
            if self.map[current[1]][current[0]] == target:
                return self.reconstruct_path(came_from, current)

            for (dx, dy), dir in directions.items():
                neighbor = (current[0] + dx, current[1] + dy)

                if self.is_within_bounds(neighbor) and self.map[neighbor[1]][neighbor[0]] != '#':  # Avoid walls
                    tentative_g_score = g_score[current] + 1

                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, target_tile=target)
                        if neighbor not in [i[1] for i in open_set]:
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None  # Return None if no path to the base is found

    def heuristic(self, position, target_tile='b'):
        """
        Heuristic function for A* (Manhattan distance).
        """
        base_pos = self.find_target_tile(target_tile)
        return abs(position[0] - base_pos[0]) + abs(position[1] - base_pos[1])

    def find_target_tile(self, target_tile):
        """
        Find the first occurrence of the target tile on the map (e.g., 'b' for base).
        """
        for y in range(len(self.map)):
            for x in range(len(self.map[0])):
                if self.map[y][x] == target_tile:
                    return (x, y)
        return None  # Return None if target tile is not found
    
    def bfs_find_path(self, start, target='r'):
        """
        Find the shortest path to the nearest tile matching the target symbol.
        Returns a list of coordinates to reach the target tile.
        """
        queue = deque([(start, [])])  # Queue stores tuples of (current_position, path_to_current)
        visited = set([start])  # Set of visited positions to avoid cycles
        
        directions = {
            (0, -1): 'N',
            (0, 1): 'S',
            (-1, 0): 'W',
            (1, 0): 'E'
        }
        
        while queue:
            (x, y), path = queue.popleft()
            
            # Check if we've reached the target
            if self.map[y][x] == target:
                return path + [(x, y)]  # Return the path including the target tile
            
            # Explore neighboring positions
            for (dx, dy), dir in directions.items():
                neighbor = (x + dx, y + dy)
                
                if self.is_within_bounds(neighbor) and neighbor not in visited:
                    nx, ny = neighbor
                    if self.map[ny][nx] != '#':  # Avoid walls
                        visited.add(neighbor)
                        queue.append((neighbor, path + [(x, y)]))

        return None  # Return None if no path to the target is found

    def get_direction(self, start, next_position):
        """
        Determine direction based on the difference between current and next position.
        """
        dx = next_position[0] - start[0]
        dy = next_position[1] - start[1]
        
        if dx == 0 and dy == -1:
            return 'N'
        elif dx == 0 and dy == 1:
            return 'S'
        elif dx == -1 and dy == 0:
            return 'W'
        elif dx == 1 and dy == 0:
            return 'E'
        return None

    def is_within_bounds(self, position):
        x, y = position
        return 0 <= y < len(self.map) and 0 <= x < len(self.map[0])
    
    from collections import deque

if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '0.0.0.0'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
