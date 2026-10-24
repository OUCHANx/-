"""Build Metricool update payloads for the v2 reels (new video, custom cover, one sound-on line in the caption)."""
import json

RAW = "https://raw.githubusercontent.com/OUCHANx/-/jacob-assets/month/"
posts = json.load(open("/home/claude/reel/v2/out/scheduled_reels.json"))

SOUND_LINES = [
    "音を出して聞くと、発音もいっしょに覚えられるよ。",
    "音声つきだから、声に出してマネしてみてね。",
    "発音は音を出してチェックしてみてね。",
    "聞きながら、いっしょに言ってみてね。",
]


def add_sound_line(text, i):
    if "音" in text and ("発音" in text or "音声" in text):
        return text
    line = SOUND_LINES[i % len(SOUND_LINES)]
    parts = text.rstrip().split("\n\n")
    if parts[-1].lstrip().startswith("#"):
        parts.insert(len(parts) - 1, line)
    else:
        parts.append(line)
    return "\n\n".join(parts)


out = []
for i, p in enumerate(posts):
    date = p["dt"][:10]
    info = {
        "autoPublish": True,
        "descendants": [],
        "draft": False,
        "firstCommentText": "",
        "hasNotReadNotes": False,
        "media": [RAW + f"reels_v2/{date}.mp4"],
        "videoThumbnailUrl": RAW + f"covers/{date}.jpg",
        "mediaAltText": [],
        "providers": [{"network": "instagram"}],
        "publicationDate": {"dateTime": p["dt"], "timezone": "Asia/Tokyo"},
        "shortener": False,
        "smartLinkData": {"ids": []},
        "text": add_sound_line(p["text"], i),
        "instagramData": {"type": "REEL", "showReelOnFeed": True, "isAiGenerated": True, "autoPublish": True},
    }
    out.append({"date": date, "id": str(p["id"]), "uuid": p["uuid"], "info": json.dumps(info, ensure_ascii=False)})

json.dump(out, open("/home/claude/reel/v2/out/updates.json", "w"), ensure_ascii=False, indent=1)
print(len(out))
print(json.loads(out[0]["info"])["text"])
print("----")
print(json.loads(out[5]["info"])["text"])
