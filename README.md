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
