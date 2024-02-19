# suburb
## The Sburb Simulator

A work-in-progress version of Suburb, the spiritual successor to the [Overseer Project](https://github.com/TheOverseerProject/OverseerLegacy). 

This game attempts to semi-accurately simulate the experience of playing the fictional game Sburb, which appears in the webcomic Homestuck. It takes some additional creative liberties, but none that aren't in the spirit of the comic.

In order to host the game in its current state, you'll need to get a valid SSL certificate and key authorized by a CA. The client also automatically connects to suburbgame.com hosted on port 25565, so you will need to change this in client.py. Later, I plan on hosting a full-time server and making builds to publically release. I also plan on implementing support for other servers within the client itself.

The game is currently in an unstable Alpha state. Expect crashes and errors. Please do not re-use passwords for accounts on this service; to the best my knowledge the server data transfer and storage is secure, but I am an amateur and don't have experience with data transfer protocols or encryption except for this project and I haven't had anyone I trust look at things yet.

The main server is not up 24/7 and I usually only keep it up when playtest sessions are happening. If you want to stay updated with the game's development, contribute, or just want to participate in playtest sessions in its current state, consider joining the [Discord server](https://discord.gg/k2uuDc9fvF).
