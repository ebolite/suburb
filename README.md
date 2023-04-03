# suburb
The Sburb Simulator

A work-in-progress version of Suburb. 

This game attempts to semi-accurately simulate the experience of playing the fictional game Sburb, which appears in the webcomic Homestuck. It takes some additional creative liberties, but none that aren't in the spirit of the comic.

In order to host the game in its current state, you'll need to get a valid SSL certificate and key authorized by a CA, and connect to MongoDB Atlas to store data. The client also automatically connects to suburbgame.com hosted on port 25565, so you will need to change this in client.py. Later, I plan on hosting a full-time server and making builds to publically release.
