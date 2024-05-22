# GameID
Identify a game using [GameDB](https://github.com/niemasd/GameDB). Supported consoles:

* `GC` - Nintendo GameCube
* `PSX` - Sony PlayStation
* `PS2` - Sony PlayStation 2

## Usage

```
usage: GameID.py [-h] -i INPUT -c CONSOLE -d DATABASE [-o OUTPUT] [--delimiter DELIMITER] [--prefer_gamedb]

options:
  -h, --help                         show this help message and exit
  -i INPUT, --input INPUT            Input Game File (default: None)
  -c CONSOLE, --console CONSOLE      Console (options: GC, PS2, PSX) (default: None)
  -d DATABASE, --database DATABASE   GameID Database (db.pkl.gz) (default: None)
  -o OUTPUT, --output OUTPUT         Output File (default: stdout)
  --delimiter DELIMITER              Delimiter (default: '\t')
  --prefer_gamedb                    Prefer Metadata in GameDB (rather than metadata loaded from game) (default: False)
```

### Example: Identify a Game

```bash
./GameID.py -d db.pkl.gz -c <CONSOLE> -i <GAME_FILE>
```

### Example: Identify All PSX Games in Directory (recursive)

```bash
find psx_games/ -type f -iname "*.cue" -o -iname "*.iso" | parallel --jobs 8 ./GameID.py -d db.pkl.gz -c PSX -i "{}" ">" "{}.meta.txt"
```

### Build Database

```bash
rm -f db.pkl.gz && ./scripts/build_db.py db.pkl.gz
```
