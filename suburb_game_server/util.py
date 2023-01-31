import os
homedir =  os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game_server" in subdirectories: # if this is being run in vscode lol
    homedir += "\\suburb_game_server"

sessions = {}
