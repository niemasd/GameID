import ConsoleID

if ('args' in globals()):
    # set command line arguments, from javascript
    ConsoleID.sys.argv = args.split()
    ConsoleID.main()