import GameID

if ('args_GameID' in globals()):
    # set command line arguments, from javascript
    GameID.sys.argv = args_GameID.split()
    GameID.main()
