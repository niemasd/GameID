# GameID
Identify a game using [GameDB](https://github.com/niemasd/GameDB). Supported consoles:

* `GB` - Nintendo Game Boy
* `GBA` - Nintendo Game Boy Advance
* `GBC` - Nintendo Game Boy Color
* `GC` - Nintendo GameCube
* `Genesis` - Sega Genesis
* `N64` - Nintendo 64
* `NeoGeoCD` - SNK Neo Geo CD
* `PS2` - Sony PlayStation 2
* `PSP` - Sony PlayStation Portable
* `PSX` - Sony PlayStation
* `Saturn` - Sega Saturn
* `SegaCD` - Sega CD
* `SNES` - Super Nintendo Entertainment System

## Usage

For manually checking individual games, we recommend using the [GameID web app](https://niema.net/GameID). For bulk/programmatic lookups, we recommend using the command line Python script, [`GameID.py`](GameID.py):

```
usage: GameID.py [-h] -i INPUT -c CONSOLE [-d DATABASE] [-o OUTPUT] [--delimiter DELIMITER] [--prefer_gamedb]

options:
  -h, --help                         show this help message and exit
  -i INPUT, --input INPUT            Input Game File (default: None)
  -c CONSOLE, --console CONSOLE      Console (options: GC, N64, PS2, PSX) (default: None)
  -d DATABASE, --database DATABASE   GameID Database (db.pkl.gz) (default: None)
  -o OUTPUT, --output OUTPUT         Output File (default: stdout)
  --delimiter DELIMITER              Delimiter (default: '\t')
  --prefer_gamedb                    Prefer Metadata in GameDB (rather than metadata loaded from game) (default: False)
```

If the database ([`db.pkl.gz`](db.pkl.gz)) is not provided via `-d`, it will be downloaded from this repo. This is **very slow**, so we strongly recommend providing it if you are running GameID in bulk (or if your environment does not have internet connection).

This tool is being actively developed, and updates will be pushed somewhat frequently. As such, be sure to periodically `git pull` an up-to-date version of this repository to ensure you have access to all of the latest features and optimizations.

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

## Acknowledgements

* Thanks to [MiSTer Addons](https://misteraddons.com/) for the idea and for help with testing!
* Thanks to [Artemio Urbina](https://junkerhq.net/) and the other developers of the [240p Test Suite](https://artemiourbina.itch.io/240p-test-suite), which we use as an example file!
* Thanks to [Daniel Ji](https://github.com/daniel-ji) for creating the Pyodide web app!
* Site favicon by open source project [Twemoji](https://github.com/twitter/twemoji") licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
