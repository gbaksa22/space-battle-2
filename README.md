AO RTS
======


## Goal

Write an AI to command your troops to gather the most resources in the time allotted. The AI communicates over TCP via a JSON protocol.

***

## API

The server will connect to your client. You will start receiving messages in the format:

    {
      player: 0,
      turn: 12,
      time: 300000, // time remaining in game
      'unit_updates': [{ // your unit's updates
        id:16,
        player_id: 0,
        x: 0, y: 0,
        status:"moving",
        type:"worker",
        resource:0,
        health:5,
        can_attack:true // cooldown is ready
      }],
      'tile_updates': [{
        // relative to your base
        x: 7, y: -9,
        visible: true,
        blocked: false,
        resources: {
          id: 12,
          type: "small",
          total:200,
			value:10
        },
        units: [{
          id:60,
          type:"tank",
          status:"unknown", // tile update statuses can only be unknown or dead
          player_id: 1,
          health: 10
        }]}
      ],
    }
    
To command your units:


    {
      commands: [
        {command: "MOVE", unit: 2, dir: "N"},
        {command: "MOVE", unit: 3, dir: "S"},
        {command: "GATHER", unit: 7, dir: "S"},
        {command: "CREATE", type: "worker"},
        {command: "SHOOT", unit: 4, dx: 3, dy: 2},
        {command: "MELEE", unit: 4, target: 2},
      ]
    }

#### Warning!

    The protocol is newline delimited. Make sure your JSON has all but its last newline stripped!


##### unit_updates
Any time something one of your units changes, (position, status, etc), you will receive an update.

##### tile_updates
Any time something about a tile changes, (enemy units, visibility, etc), you will receive an update.

##### time
This is the amount of time remaining in the game (in milliseconds). 

##### turn
This is the current turn of the game. Each turn is 200ms.

***

## Commands

Commands are your AIs way of telling the server what you want your units to do. Some commands take many turns to complete. When finished executing a command, a unit's status will be set to `idle`.

__MOVE__: `unit`,`dir` Move a unit by id in a given direction `N,S,E,W`. Command will be ignored if the unit cannot move in the specified direction or is currently executing a previous `MOVE` command.

__GATHER__: `unit`,`dir` Tell a unit to collect from a resource in the specified direction `N,S,E,W`. Command will be ignored if the unit cannot gather in the specified direction. Resources are automatically deposited by walking over the players base.

__CREATE__: `type` Create a new unit by type: `worker,scout,tank`. Command is ignored if the player's base does not have enough resources.

__SHOOT__: `unit`,`dx`,`dy` Tell the unit to shoot a location relative to the attacker. All units at the location will be damaged (including your own). Command is ignored if the location is out of the attacker's range (within unit vision). Each unit has an attack cooldown. `can_attack` will be sent down as `true` when they can attack again.

__MELEE__: `unit`,`target` Tell the unit to melee a nearby unit. Command is ignored if target unit is more than a single tile away. Each unit has an attack cooldown. `can_attack` will be sent down as `true` when they can attack again.

####Note:
    When a unit has died, its status will be set to "dead".
    Dead units will no longer respond to your commands.
***


## Units
![base](server/assets/PNG/Retina/Structure/scifiStructure_11.png "base")

__BASE__: When joining the game, your base will be placed at a random location on the map. Any map location will be sent from the server relative to your base's location.

![worker](https://gitlab.atomicobject.com/shawn.anderson/ao-rts/raw/master/server/assets/PNG/Retina/Unit/scifiUnit_02.png "worker")

__WORKER__: You will start the game with 6 workers. Workers are the only unit that can carry resources. They have average vision, speed, health, and a weak melee attack. Cost: 100.

![scout](https://gitlab.atomicobject.com/shawn.anderson/ao-rts/raw/master/server/assets/PNG/Retina/Unit/scifiUnit_06.png "scout")

__SCOUT__: Scouts have longer vision, faster speed, lower health, and a weak melee attack. Cost 130.

![tank](https://gitlab.atomicobject.com/shawn.anderson/ao-rts/raw/master/server/assets/PNG/Retina/Unit/scifiUnit_08.png "tank")

__TANK__: Tanks have average vision, slower speed, higher health, and a ranged attack. Cost 150.

| type   | cost | range (+/-) | speed (tpt<sup>*</sup>) | health | attack cooldown (turns) | build time (turns) |
|--------|------|-------|-------|--------|-----------------|---|
| worker | 100  | 2     | 5     | 5      | 3 | 5  |
| scout  | 130  | 2     | 5     | ?      | 3 | 10 |
| tank   | 150  | 2     | 5     | ?      | 5 | 15 |

<sup>*</sup>__turns per tile (tpt):__ Number of turns required to move from one grid location to the next. smaller is faster.

***

## Communication Overview

WIP

## JSON Schema

###Message from Server

| property | type | notes |
|----------|------|-------|
| `time` | `int` | Milliseconds left in the game |
| `turn` | `int` | Current turn of the game |
| `player_id` | `int` | Your player id |
| `tile_updates` | `array of Tiles` | Tiles that changed last turn |
| `unit_updates` | `array of Units` | Your units that changed last turn |

#### Unit
| property | type | notes |
|----------|------|-------|
| `id` | `int` | Unique identifier for the unit. |
| `player_id` | `int` | Your player identifier. |
| `x` | `int` | Tile coord (positive to the right "E") |
| `y` | `int` | Tile coord (positive is down "S") |
| `type` | `string` | Type of unit (base, worker, scout, tank) |
| `status` | `string` | current status (idle,moving,building,dead) |
| `health` | `int` | Current health of unit |
| `resource`__*__ | `int` | Value of resources currently being carried. |
| `can_attack`__*__ | `bool` | Can attack next turn (based on cooldown) |

__* Optional:__ may or may not be present depending on the unit type.

#### Tile
| property | type | notes |
|----------|------|-------|
| `visible` | `bool` | Can currently be seen by one of your units |
| `x` | `int` | Tile coord (positive to the right "E") |
| `y` | `int` | Tile coord (positive is down "S") |
| `blocked` | `bool` | Tile can be walked on by units. |
| `resources` | `null` or `Tile Resource` | Description of the resource (if any) on this tile. |
| `units` | `array of Enemy Units` | Enemies found on this tile. |

#### Tile Resource
| property | type | notes |
|----------|------|-------|
| `id` | `int` | Unique identifier for this resource. |
| `type` | `string` | Time of resource (small or large) |
| `total` | `int` | Total amount of value left in this resource. |
| `value` | `int` | Value of a single harvested load. |
          
#### Enemy Units

| property | type | notes |
|----------|------|-------|
| `id` | `int` | Unique identifier for the unit. |
| `type` | `string` | Type of unit (base, worker, scout, tank) |
| `status` | `string` | limited current status (dead or unknown) |
| `player_id` | `int` | Identifier of the player that owns the unit |
| `health` | `int` | Current health of unit |



## Setting Up the game

* checkout repo
* install ruby 2.3.x or newer
* install [Gosu](https://www.libgosu.org/ruby.html) dependencies ([mac](https://github.com/gosu/gosu/wiki/Getting-Started-on-OS-X) | [linux](https://github.com/gosu/gosu/wiki/Getting-Started-on-Linux))
* install bundler
* cd server
* bundle install
* ruby src/app.rb
    
## Running the game

	$ruby src/app.rb --help
	usage: src/app.rb [options]
    -p1,  --p1_host  player 1 host, default localhost
    -p1p, --p1_port  player 1 port, default 9090
    -p2,  --p2_host  player 2 host
    -p2p, --p2_port  player 2 port
    -m,   --map      map filename to play (tmx format)
    -q,   --quiet    suppress output (quiet mode)
    -l,   --log      log entire game
    -f,   --fast     advance to the next turn as soon as all clients have sent a message
    -nu,  --no_ui    No GUI; exit code is winning player
    -t,   --time     length of game in ms
    --help           print this help

**Notes**

1. Disconnecting. Game will continue, but you will lose control of your units.
2. Games are logged to game-log.txt.
