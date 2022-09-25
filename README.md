# jamulus-discord-glue
The [glue code](https://en.wikipedia.org/wiki/Glue_code) between [gojam](https://github.com/dtinth/gojam) and [pcm2discord](https://github.com/dtinth/pcm2discord), written in Python.

## Assumptions

- Docker is installed on the machine.
- pcm2discord is running with API exposed at `http://localhost:28280`
- There is a Docker image `gojam` on the host.

## Behavior

- When someone listens on the Discord channel, start streaming sound from Jamulus to Discord.
- When no one is listening on the Discord channel, stop streaming.
