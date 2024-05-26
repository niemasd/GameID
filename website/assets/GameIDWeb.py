import GameID

if ('args' in globals()):
    # set command line arguments, from javascript
    GameID.sys.argv = args.split()
    GameID.main()