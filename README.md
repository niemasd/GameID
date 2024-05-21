# GameID
Identify a game using [GameDB](https://github.com/niemasd/GameDB)

## Usage

### Build Database

```bash
rm -f db.pkl.gz && ./build_db.py db.pkl.gz
```

### Identify a Game

```bash
./GameID.py -d db.pkl.gz -c <CONSOLE> -i <GAME_FILE>
```

### Identify All PSX Games in Directory (recursive)

```bash
find psx_games/ -type f -iname "*.cue" -o -iname "*.iso" | parallel --jobs 8 ./GameID.py -d db.pkl.gz -c PSX -i "{}" ">" "{}.meta.txt"
```
