import ConsoleID

if ('args_ConsoleID' in globals()):
    # set command line arguments, from javascript
    ConsoleID.sys.argv = args_ConsoleID.split()
    ConsoleID.main()
