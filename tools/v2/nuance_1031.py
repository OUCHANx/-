"""10/31 review: replace the five remaining "mistake" reels (classic katakana-English, 2-3% past 3 s)
with harder "hard-to-translate Japanese" topics built on the ranking template (best 3-second hold).

usage:
  python3 nuance_1031.py render [dates]   # mp4 + cover + sheet into out/ as <date>-b.*
  python3 nuance_1031.py asr              # rough intelligibility check of every new voiced line
  python3 nuance_1031.py payloads         # Metricool update payloads -> out/nuance_updates.json
"""
import json, os, shutil, sys

sys.path.insert(0, "/home/claude/reel/v2")
sys.path.insert(0, "/home/claude/reel")
import reel_v2 as rv
import content

PURPLE = (118, 86, 168)

NEW = [
    {"date": "2026-11-03", "kind": "nuance",
     "hook": "「懐かしい〜！」って\n英語で言える？",
     "title": "「懐かしい！」の\n言い方 3選",
     "ranks": [["Good times!", "あの頃は楽しかったね", "思い出話をしながら、しみじみと"],
               ["That brings back memories.", "いろいろ思い出すなあ", "写真や曲で思い出がよみがえったとき"],
               ["This takes me back!", "うわ、懐かしい！", "「懐かしい！」にいちばん近いひとこと"]],
     "end": "保存して、\n思い出話で使ってみてね",
     "caption": "「懐かしい！」は、英語にぴったりの一語がない言葉。\n“nostalgic” も使えるけど、昔の写真や曲を見て思わず出る「懐かしい〜！」は “This takes me back!” がしっくりくるよ。",
     "sound": "聞きながら、いっしょに言ってみてね。",
     "tags": "#英会話 #英語勉強中 #ネイティブ表現 #ジェイコブ",
     "id": "404986098", "uuid": "-5851205273374601820", "rtitle": "「懐かしい！」英語で言える？"},
    {"date": "2026-11-07", "kind": "nuance",
     "hook": "「もったいない！」って\n英語で言える？",
     "title": "「もったいない」の\n言い方 3選",
     "ranks": [["Don't let it go to waste.", "むだにしないでね", "食べ物や才能を「むだにしないで」"],
               ["That's a shame.", "それはもったいないね", "チャンスを逃したときの「もったいない」"],
               ["What a waste!", "もったいない！", "物やお金がむだになったときの定番"]],
     "end": "保存して、\n使える場面で言ってみてね",
     "caption": "「もったいない」も、英語に一語でぴったりの言葉がないんだ。\n物がむだになるなら “What a waste!”、チャンスを逃したなら “That’s a shame.” と、場面で言い分けるのがコツ。",
     "sound": "音声つきだから、声に出してマネしてみてね。",
     "tags": "#英会話 #英語フレーズ #日常英会話 #カピバラ",
     "id": "404986392", "uuid": "-3023420020954345847", "rtitle": "「もったいない」英語で言える？"},
    {"date": "2026-11-11", "kind": "nuance",
     "hook": "「しょうがないね」って\n英語で言える？",
     "title": "「しょうがない」の\n言い方 3選",
     "ranks": [["There's nothing we can do.", "どうしようもないね", "打つ手がないときの「しょうがない」"],
               ["Oh well.", "まあ、いっか", "軽く気持ちを切りかえるときに"],
               ["It is what it is.", "しょうがないよ", "変えられないことを受け入れるときに"]],
     "end": "保存して、\nあとで使ってみてね",
     "caption": "「しょうがない」は辞書だと “It can’t be helped.” だけど、会話では “It is what it is.” をよく聞くよ。\n軽く流すなら “Oh well.” でOK。",
     "sound": "聞きながら、いっしょに言ってみてね。",
     "tags": "#英語学習 #英会話初心者 #使える英語 #カピバラ",
     "id": "404986586", "uuid": "-8733795773342465743", "rtitle": "「しょうがない」英語で言える？"},
    {"date": "2026-11-15", "kind": "nuance",
     "hook": "「めんどくさ〜い」って\n英語で言える？",
     "title": "「めんどくさい」の\n言い方 3選",
     "ranks": [["I don't feel like it.", "なんか気が乗らない", "やる気が出ないときの「めんどくさい」"],
               ["It's such a hassle.", "ほんと手間だなあ", "手続きや準備がめんどうなときに"],
               ["What a pain!", "めんどくさい！", "気軽にぼやくときの定番"]],
     "end": "保存して、\nあとで使ってみてね",
     "caption": "「めんどくさい」は、何がめんどうかで言い方が変わるよ。\n手間がかかるなら “It’s such a hassle.”、やる気が出ないだけなら “I don’t feel like it.”",
     "sound": "音声つきだから、声に出してマネしてみてね。",
     "tags": "#英会話 #英語勉強中 #ネイティブ表現 #ジェイコブ",
     "id": "404987320", "uuid": "-5153781015684888004", "rtitle": "「めんどくさい」英語で言える？"},
    {"date": "2026-11-19", "kind": "nuance",
     "hook": "「気まずい…」って\n英語で言える？",
     "title": "「気まずい」の\n言い方 3選",
     "ranks": [["There was an awkward silence.", "気まずい沈黙が流れた", "会話が止まってしまったときに"],
               ["Things got weird.", "なんか気まずくなった", "関係がぎくしゃくしたときに"],
               ["This is awkward.", "気まずいな…", "その場で言える定番のひとこと"]],
     "end": "保存して、\nあとで使ってみてね",
     "caption": "「気まずい」は awkward を覚えておけば、まず大丈夫。\nその場なら “This is awkward.”、関係がぎくしゃくしたなら “Things got weird.” もよく使うよ。",
     "sound": "聞きながら、いっしょに言ってみてね。",
     "tags": "#英会話 #英語フレーズ #日常英会話 #カピバラ",
     "id": "404987373", "uuid": "-4357346485260434029", "rtitle": "「気まずい」英語で言える？"},
]
BY_DATE = {d["date"]: d for d in NEW}

# register the new series on top of the ranking template
rv.SERIES["nuance"] = ("訳しにくい日本語", PURPLE)
rv.HOOK_POSE["nuance"] = "thinking"
rv.POSE_CYCLE["nuance"] = ["thinking", "surprised", "worried"]
rv.TEMPLATE["nuance"] = rv.reel_ranking
rv.AUDIO["nuance"] = dict(key=3, bpm=94)
content.REELS[:] = [BY_DATE.get(x["date"], x) for x in content.REELS]

OUT = rv.OUT
RAW = "https://raw.githubusercontent.com/OUCHANx/-/jacob-assets/month/"


def backup(date):
    for sub, ext in (("reels", "mp4"), ("covers", "jpg")):
        src = OUT + f"{sub}/{date}.{ext}"
        dst_dir = OUT + f"{sub}_mistake_old/"
        os.makedirs(dst_dir, exist_ok=True)
        if os.path.exists(src) and not os.path.exists(dst_dir + f"{date}.{ext}"):
            shutil.copy2(src, dst_dir + f"{date}.{ext}")


def render(date):
    backup(date)
    d = BY_DATE[date]
    r = rv.reel_ranking(d)
    mp4 = OUT + f"reels/{date}-b.mp4"
    r.export(mp4, rv.AUDIO["nuance"])
    cov = rv.cover(date)  # writes covers/<date>.jpg
    shutil.move(cov, OUT + f"covers/{date}-b.jpg")
    old = OUT + f"covers_mistake_old/{date}.jpg"
    if os.path.exists(old):
        shutil.copy2(old, OUT + f"covers/{date}.jpg")  # keep the old cover file in place
    sh, dur, voices = rv.sheet(date, [0, 0.8, 1.6, 2.6, 3.6, 5.5, 8.0, 11.0, 13.5, r.dur - 0.4])
    shutil.move(sh, OUT + f"sheets/{date}-b.png")
    return round(r.dur, 2), voices


def payloads():
    out = []
    for d in NEW:
        text = d["caption"] + "\n\n" + d["sound"] + "\n\n" + d["tags"]
        info = {"autoPublish": True, "descendants": [], "draft": False, "firstCommentText": "",
                "hasNotReadNotes": False, "media": [RAW + f"reels_v2/{d['date']}-b.mp4"],
                "videoThumbnailUrl": RAW + f"covers/{d['date']}-b.jpg", "mediaAltText": [],
                "providers": [{"network": "instagram"}],
                "publicationDate": {"dateTime": f"{d['date']}T20:00:00", "timezone": "Asia/Tokyo"},
                "shortener": False, "smartLinkData": {"ids": []}, "text": text,
                "instagramData": {"type": "REEL", "showReelOnFeed": True, "isAiGenerated": True, "autoPublish": True}}
        out.append({"date": d["date"], "id": d["id"], "uuid": d["uuid"],
                    "info": json.dumps(info, ensure_ascii=False, separators=(",", ":"))})
    json.dump(out, open(OUT + "nuance_updates.json", "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "render":
        for dt in (sys.argv[2:] or sorted(BY_DATE)):
            print(dt, render(dt), flush=True)
    elif cmd == "asr":
        sys.argv = [sys.argv[0]]
        from asr_check import asr, wer  # noqa: E402  (module runs its own demo only with argv voices)
        E = N = 0
        for d in NEW:
            for en, _, _ in d["ranks"]:
                s = rv.tts(en, rv.MODEL_VOICE, 0.92)
                h = asr(s.astype("float64"), rv.SR)
                e, n = wer(rv.clean(en), h); E += e; N += n
                print(f"{d['date']}  {en:32} -> {h}")
        print("WER", round(E / N, 2))
    elif cmd == "payloads":
        for p in payloads():
            print(p["date"], json.loads(p["info"])["text"].replace("\n", " / ")[:160])
