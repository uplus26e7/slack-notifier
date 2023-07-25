import typer
from dotenv import load_dotenv
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import re
import requests
import json
import subprocess
from tempfile import NamedTemporaryFile

load_dotenv()

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
VOICEBOX_BASE_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 8

app = App(
    token=BOT_TOKEN,
    signing_secret=SIGNING_SECRET,
)


@app.event("app_mention")
def handle_mention(body):
    message = parse_mention(body)
    typer.echo(f"message: {message}")

    audio = generate_audio(text=message)

    with NamedTemporaryFile("wb") as fp:
        fp.write(audio)
        subprocess.run(["afplay", fp.name])


def parse_mention(body) -> str:
    event = body["event"]
    message = re.sub(r"<@.*?>", "", event["text"]).strip()
    return message


def generate_audio(text: str):
    res_query = requests.post(
        f"{VOICEBOX_BASE_URL}/audio_query",
        params={
            "text": text,
            "speaker": SPEAKER_ID,
        },
    )
    assert res_query.ok

    res_synth = requests.post(
        f"{VOICEBOX_BASE_URL}/synthesis",
        params={"speaker": SPEAKER_ID},
        data=json.dumps(res_query.json()),
    )
    assert res_synth.ok

    return res_synth.content


def main():
    handler = SocketModeHandler(app, APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    typer.run(main)
