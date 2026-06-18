#!/usr/bin/env python3
"""Scrape a lyrics page's raw HTML and extract just the lyric block.
Usage: fetch_lyrics.py <url>  -> prints clean lyrics to stdout."""
import sys, re, html, urllib.request

JUNK = re.compile(r"(?i)текст песни|слова песни|все тексты|перевод|скачать|"
                  r"смотреть|поиск|главная|реклама|комментар|похож|рейтинг|"
                  r"добавить|войти|регистрац|перейти к|©|cookie|клип на|видео|тексты песен|"
                  r"исполнит|альбом|аккорд|popular|караоке|просмотр|официальн|"
                  r"читать|слушать|музыка|жанр|год выпуска|длительност")

HARD_STOP = re.compile(r"(?i)популярн|оценок|права на|следите за|правооблад|"
                       r"другие песни|похожие|комментар|смотрите также")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</(p|div)>", "\n", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return [l.strip() for l in html.unescape(raw).splitlines()]

def is_lyric(l):
    return (3 < len(l) < 90 and re.search("[а-яёА-ЯЁ]", l)
            and not JUNK.search(l) and len(re.findall(r"[а-яёА-ЯЁ]", l)) > len(l) * 0.4)

def extract(lines):
    # lyric region = first lyric line .. last; junk -> stanza break; collapse blanks
    idx = [i for i, l in enumerate(lines) if is_lyric(l)]
    if not idx:
        return []
    out = []
    for l in lines[idx[0]:idx[-1] + 1]:
        if HARD_STOP.search(l):
            break
        if is_lyric(l):
            out.append(l)
        elif out and out[-1] != "":
            out.append("")
    while out and out[-1] == "":
        out.pop()
    return out

if __name__ == "__main__":
    print("\n".join(extract(fetch(sys.argv[1]))))
