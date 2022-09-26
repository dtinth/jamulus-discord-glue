import requests
import time
import os
from dotenv import load_dotenv
from sqlitedict import SqliteDict

load_dotenv()

db = SqliteDict("/tmp/jamchatbridge.sqlite", autocommit=True)

last_name = None


def start_gojam():
    global last_name
    os.system(
        "docker run -d --name=gojam --network=host --rm --init gojam gojamclient --server 150.95.25.226:22124 --pcmout 127.0.0.1:28282 --apiserver 127.0.0.1:28281 --name 'Discord' --vad"
    )
    last_name = None


def stop_gojam():
    os.system("docker stop gojam")
    os.system("docker rm -f gojam 2>&1")


def is_gojam_running():
    return is_docker_container_running("gojam")


def is_docker_container_running(name):
    return os.system('test -n "$(docker ps -q -f name=%s)"' % name) == 0


while True:
    try:
        # Get the count of listeners from Discord
        r = requests.get("http://localhost:28280/count")

        # Response is in form: { "listening": 2 }
        # Get the number of listeners
        listeners = r.json()["listening"]
        gojam_running = is_gojam_running()

        # Check if the `gojam` Docker container is running
        if listeners > 0 and not gojam_running:
            print("Starting gojam")
            start_gojam()
        elif listeners == 0 and gojam_running:
            print("Stopping gojam")
            stop_gojam()
        elif gojam_running:
            # Submit the number of listeners to channel info endpoint
            # $ http patch localhost:9999/channel-info name=$listeners
            name = " Discord[" + str(listeners) + "]"
            r = requests.patch(
                "http://localhost:28281/channel-info", json={"name": name}
            )

            if last_name != name:
                print(
                    "Updated channel name to "
                    + name
                    + " at "
                    + time.strftime("%H:%M:%S")
                )
                last_name = name

        # Load chat messages from Discord
        r = requests.get("http://localhost:28280/chat").json()

        # Iterate over messages
        for message in r:
            if message["id"] in db:
                continue
            if gojam_running:
                # Send message to gojam
                body = {
                    "message": "(From Discord) "
                    + message["from"]
                    + ": "
                    + message["message"]
                }
                r = requests.post(
                    "http://localhost:28281/chat",
                    json=body,
                )
                print("Sent message", message)
            else:
                print("Skip message", message)
            db[message["id"]] = True

        # Load chat messages from gojam
        if gojam_running:
            r = requests.get("http://localhost:28281/chat").json()

            # Iterate over messages
            for message in r:
                if message["id"] in db:
                    continue

                html = message["message"]

                # A valid message is formatted like this:
                # <font color="red">(12:27:04 AM) <b>dtinth  testing</b></font> ok
                # We want to extract the name and text.

                # First, ensure it starts with `<font`
                if not html.startswith("<font"):
                    continue

                # Next, get the text in <b>
                name = html.split("<b>")[1].split("</b>")[0]

                # Finally, get the text after the name
                text = html.split("</font>")[1]

                # If name is a Discord bot (i.e. contains "Discord["), skip
                if "Discord[" in name:
                    continue

                # Send message to Discord
                body = {
                    "content": text,
                    "username": name + " (Jamulus)",
                }
                webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
                r = requests.post(
                    webhook_url,
                    json=body,
                )
                print("Sent message", message)
                db[message["id"]] = True
    except Exception as e:
        print("Error: {}".format(e))
    finally:
        # Wait 2 seconds
        db.commit()
        time.sleep(2)
