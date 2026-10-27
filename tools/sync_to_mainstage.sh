#!/usr/bin/env bash
# Sync rendered playback stems from the source pipeline into the keyboardist's
# MainStage rig repo (cherry-daddies-2000) and optionally commit.
#
# Mechanics:
#   - For each setlist song it copies ONLY the stems that already exist in the
#     target folder (click/cues/pb-other/pb-bass), overwriting in place.
#   - It never adds or removes stem files. MainStage references audio by path;
#     a brand-new or renamed stem needs a manual patch edit in MainStage, so the
#     script deliberately won't introduce one. Same reason it won't delete.
#   - Source = <song>/auto-render/<stem>.wav ; all.wav / cue_preview.mp3 /
#     timeline.json are pipeline-internal and never copied.
#
# Usage:
#   tools/sync_to_mainstage.sh                 # sync every song (dry-run summary first)
#   tools/sync_to_mainstage.sh --apply         # actually copy
#   tools/sync_to_mainstage.sh --apply "S&M"   # only songs whose mapping matches the filter
#   tools/sync_to_mainstage.sh --apply --commit "S&M: re-render cues"
#                                              # copy, then git add+commit in the rig repo (no push)
#
# Default is dry-run: shows what WOULD change. Add --apply to write files.

set -euo pipefail

SRC_ROOT="/Users/alex/projects/cherry-daddies/music/songs"
RIG_ROOT="/Users/alex/projects/cherry-daddies-2000"
SETLIST_DIR="$RIG_ROOT/cherry-daddies-setlist-2026-06-16"

# setlist-folder ||| source-song-folder
MAP=(
  "01 Better Off Alone|||Alice Deejay - Better Off Alone"
  "03 Whenever, Wherever|||Shakira - Whenever, Wherever"
  "04 Infinity 2008|||Guru Josh - Infinity 2008"
  "05 Mr. Saxobeat|||Alexandra Stan - Mr. Saxobeat"
  "07 Adventure of a Lifetime|||Coldplay - Adventure of a Lifetime"
  "08 Blinding Lights|||The Weeknd - Blinding Lights"
  "10 Freed From Desire|||Gala - Freed from Desire"
  "11 Uptown Funk|||Bruno Mars & Mark Ronson - Uptown Funk"
  "12 Солнышко|||Demo - Solnyshko"
  "13 Про красивую жизнь|||Band'Eros - Pro krasivuju zhizn'"
  "15 Я устал|||Quest Pistols - Я устал"
  "16 Now You're Gone|||Basshunter - Now You're Gone"
  "17 S&M|||Rihanna - S&M"
  "18 Beverly Hills|||Beverly Hills"
  "19 We Found Love|||Rihanna & Calvin Harris - We Found Love"
  "20 Everytime We Touch|||Cascada - Everytime We Touch"
  "24 Я сошла с ума|||t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)"
  "A Touch of Class - Around the World (La La La La La)|||A Touch of Class - Around the World (La La La La La)"
  "Alex Gaudino - Destination Calabria|||Alex Gaudino - Destination Calabria"
  "Icona Pop & Charli XCX - I Love It|||Icona Pop & Charli XCX - I Love It"
  "Laurent Wolf & Eric Carter - No Stress|||Laurent Wolf & Eric Carter - No Stress"
  "SEREBRO - Malo tebya|||SEREBRO - Malo tebya"
  "Yeah Yeah Yeahs - Heads Will Roll|||Yeah Yeah Yeahs - Heads Will Roll"
  # tryout batch (2026-07, folders named by source song; wired manually in MainStage)
  "Мама Люба|||Мама Люба"
  "Кислотный DJ|||Кислотный DJ"
  "Такая любовь|||Такая любовь"
  "Eva 2.0|||Eva 2.0"
  "Елена Терлеева - Солнце|||Елена Терлеева - Солнце"
  "Беги от меня|||Беги от меня"
  "Медведица|||Мумий Тролль - Медведица"
  "Кукла колдуна|||Король и Шут - Кукла колдуна"
  "Ту-лу-ла|||Чичерина - Ту-лу-ла"
  "Rock & Roll Queen|||The Subways - Rock & Roll Queen"
  "Pretty Fly|||The Offspring - Pretty Fly (For A White Guy)"
  "Медляк|||Mr. Credo - Медляк"
  "Я буду|||5sta Family & 23:45 - Я буду"
  "Smells Like Teen Spirit|||Nirvana - Smells Like Teen Spirit"
  # 24.10 Lefkara batch (27 songs)
  "Heart of Glass|||Blondie - Heart of Glass"
  "Ghostbusters|||Ray Parker Jr. - Ghostbusters"
  "Venus|||Shocking Blue - Venus"
  "Cheri, Cheri Lady|||Modern Talking - Cheri, Cheri Lady"
  "Stumblin' In|||Suzi Quatro & Chris Norman - Stumblin' In"
  "Sarà perché ti amo|||Ricchi e Poveri - Sarà perché ti amo"
  "Sweet Dreams|||Eurythmics - Sweet Dreams (Are Made of This)"
  "Personal Jesus|||Depeche Mode - Personal Jesus"
  "Brother Louie|||Modern Talking - Brother Louie"
  "Hot Stuff|||Donna Summer - Hot Stuff"
  "Stayin' Alive|||Bee Gees - Stayin' Alive"
  "I Will Survive|||Gloria Gaynor - I Will Survive"
  "YMCA|||Village People - Y.M.C.A."
  "Gimme! Gimme! Gimme!|||ABBA - Gimme! Gimme! Gimme! (A Man After Midnight)"
  "I Love Rock 'n' Roll|||Joan Jett - I Love Rock 'n' Roll"
  "Felicità|||Al Bano & Romina Power - Felicità"
  "Mamma María|||Ricchi e Poveri - Mamma María"
  "It's Raining Men|||Weather Girls - It's Raining Men"
  "Maniac|||Flashdance (Michael Sembello) - Maniac"
  "Girls Just Want to Have Fun|||Cyndi Lauper - Girls Just Want to Have Fun"
  "What a Feeling|||Flashdance (Irene Cara) - What a Feeling"
  "You're My Heart, You're My Soul|||Modern Talking - You're My Heart, You're My Soul (Mix '98)"
  "Holding Out for a Hero|||Footloose (1984 film) - Holding Out for a Hero"
  "I Wanna Dance with Somebody|||Whitney Houston - I Wanna Dance with Somebody (Who Loves Me)"
  "The Best|||Tina Turner - The Best"
  "Sunny|||Boney M. - Sunny"
  "Money, Money, Money|||ABBA - Money, Money, Money"
  "What Is Love|||Haddaway - What Is Love"
)

# Stems the script is allowed to overwrite. Any pb-* variant counts (pb-other, pb-bass,
# pb-other-keys, pb-drums …) — the per-song filter below is "does the target already have it",
# so listing a stem here never CREATES one, it only keeps an existing one up to date.
STEMS=(click.wav cues.wav)
while IFS= read -r f; do STEMS+=("$f"); done < <(
  for p in "$SRC_ROOT"/*/auto-render/pb-*.wav; do [ -e "$p" ] && basename "$p"; done | sort -u)

APPLY=0
COMMIT_MSG=""
FILTER=""
CREATE_MISSING=0
while [ $# -gt 0 ]; do
  case "$1" in
    --apply)           APPLY=1; shift ;;
    --create-missing)  CREATE_MISSING=1; shift ;;
    --commit)          COMMIT_MSG="${2:-}"; shift 2 ;;
    *)                 FILTER="$1"; shift ;;
  esac
done

[ -d "$SETLIST_DIR" ] || { echo "ERROR: setlist dir not found: $SETLIST_DIR" >&2; exit 1; }

copied=0; skipped=0; missing=0; songs=0
echo "mode: $([ $APPLY -eq 1 ] && echo APPLY || echo DRY-RUN)${FILTER:+   filter=\"$FILTER\"}$([ $CREATE_MISSING -eq 1 ] && echo "   [create-missing]")"
echo

for entry in "${MAP[@]}"; do
  dst_name="${entry%%|||*}"
  src_name="${entry##*|||}"
  if [ -n "$FILTER" ] && [[ "$dst_name" != *"$FILTER"* && "$src_name" != *"$FILTER"* ]]; then
    continue
  fi
  dst="$SETLIST_DIR/$dst_name"
  src="$SRC_ROOT/$src_name/auto-render"
  if [ ! -d "$dst" ]; then
    if [ $CREATE_MISSING -eq 1 ]; then
      [ $APPLY -eq 1 ] && mkdir -p "$dst"
      echo "▸ created target dir: $dst_name"
    else
      echo "!! target missing, skip: $dst_name (pass --create-missing to create)"
      continue
    fi
  fi
  [ -d "$src" ] || { echo "!! no auto-render, skip:  $src_name"; continue; }

  songs=$((songs+1))
  echo "▸ $dst_name  ←  $src_name"
  for stem in "${STEMS[@]}"; do
    if [ ! -f "$dst/$stem" ] && [ $CREATE_MISSING -ne 1 ]; then
      continue          # only overwrite stems MainStage already references unless create-missing
    fi
    if [ ! -f "$src/$stem" ]; then
      [ -f "$dst/$stem" ] && { echo "    MISSING in render: $stem  (target has it — re-render or fix mix.json)"; missing=$((missing+1)); }
      continue
    fi
    if cmp -s "$src/$stem" "$dst/$stem"; then
      echo "    = $stem  (identical, skip)"
      skipped=$((skipped+1))
    else
      echo "    ↑ $stem  ($(du -h "$src/$stem" | cut -f1))"
      [ $APPLY -eq 1 ] && cp "$src/$stem" "$dst/$stem"
      copied=$((copied+1))
    fi
  done
done

echo
echo "songs: $songs   changed: $copied   identical: $skipped   missing-in-render: $missing"

echo
echo "=== syncing <concert>/Playback/*.wav bundles ==="
python3 - "$SRC_ROOT" "$RIG_ROOT" "$APPLY" "$FILTER" << 'PYEOF'
import os, sys, glob, re, shutil, filecmp, urllib.parse

src_root, rig_root, apply_flag, flt = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]

PATCH_TO_SONG = {
    "1__#$!@%!#__Rihanna.patch": "Rihanna & Calvin Harris - We Found Love",
    "Adventure of a Lifetime.patch": "Coldplay - Adventure of a Lifetime",
    "Akula.patch": "Кислотный DJ",
    "Alexandra Stan.patch": "Alexandra Stan - Mr. Saxobeat",
    "Alice Deejay.patch": "Alice Deejay - Better Off Alone",
    "Basshunter.patch": "Basshunter - Now You're Gone",
    "Blinding Lights.patch": "The Weeknd - Blinding Lights",
    "Cascada.patch": "Cascada - Everytime We Touch",
    "Demo.patch": "Demo - Solnyshko",
    "Destenation.patch": "Alex Gaudino - Destination Calabria",
    "Freed From Desire.patch": "Gala - Freed from Desire",
    "Guru Josh.patch": "Guru Josh - Infinity 2008",
    "I dont care.patch": "Icona Pop & Charli XCX - I Love It",
    "La la la.patch": "A Touch of Class - Around the World (La La La La La)",
    "Laurent Wolf.patch": "Laurent Wolf & Eric Carter - No Stress",
    "Quest pistols.patch": "Quest Pistols - Я устал",
    "Rihanna.patch": "Rihanna - S&M",
    "Rock & roll Queen.patch": "The Subways - Rock & Roll Queen",
    "Serebro.patch": "Мама Люба",
    "Uptown Funk.patch": "Bruno Mars & Mark Ronson - Uptown Funk",
    "beverly hills.patch": "Beverly Hills",
    "heads will roll.patch": "Yeah Yeah Yeahs - Heads Will Roll",
    "pretty fly.patch": "The Offspring - Pretty Fly (For A White Guy)",
    "tatu.patch": "t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)",
    "whenever.patch": "Shakira - Whenever, Wherever",
    "Бандерос.patch": "Band'Eros - Pro krasivuju zhizn'",
    "Беги от меня.patch": "Беги от меня",
    "Серебро.patch": "SEREBRO - Malo tebya",
    "Сольнце.patch": "Елена Терлеева - Солнце",
    "Такая любовь.patch": "Такая любовь",
    "кукла колдуна.patch": "Король и Шут - Кукла колдуна",
    "медведица.patch": "Мумий Тролль - Медведица",
    "медляк.patch": "Mr. Credo - Медляк",
    "пропоганда.patch": "Мелом",
    "тулула.patch": "Чичерина - Ту-лу-ла",
    "я буду.patch": "5sta Family & 23:45 - Я буду",
}

pb_copied = pb_skipped = 0
for cdir in sorted(glob.glob(os.path.join(rig_root, "*.concert"))):
    if not os.path.isdir(os.path.join(cdir, "Playback")):
        continue
    cname = os.path.basename(cdir)
    # Collect mappings from .cst files
    target_owners = {}  # dst_path -> list of (pname, song, kind)
    for pdir in sorted(glob.glob(os.path.join(cdir, "Concert.patch", "*.patch"))):
        pname = os.path.basename(pdir)
        song = PATCH_TO_SONG.get(pname)
        if not song:
            continue
        for cst in sorted(glob.glob(os.path.join(pdir, "*.cst"))):
            raw = open(cst, "rb").read()
            urls = [urllib.parse.unquote(m.decode("utf-8", "ignore"))
                    for m in re.findall(rb"file:///[^\x00-\x1f]+?\.wav", raw)]
            pb_urls = [u for u in urls if ".concert/Playback/" in u]
            if not pb_urls:
                continue
            rel = pb_urls[-1].replace("file:///Users/baster/Desktop/2000/", "")
            dst_p = os.path.join(rig_root, rel)
            bname = os.path.basename(dst_p)
            kind = re.sub(r"_\d+\.wav$", ".wav", bname)
            target_owners.setdefault(dst_p, []).append((pname, song, kind))

    # Also include known dedicated Playback files in 28_10_1.concert where .cst had template pb-other.wav
    if cname == "28_10_1.concert":
        extra = [
            ("La la la.patch", "A Touch of Class - Around the World (La La La La La)", "pb-other.wav", "pb-other_1.wav"),
            ("Сольнце.patch", "Елена Терлеева - Солнце", "pb-other.wav", "pb-other_10.wav"),
            ("Беги от меня.patch", "Беги от меня", "pb-other.wav", "pb-other_12.wav"),
        ]
        for pname, song, kind, fn in extra:
            dp = os.path.join(cdir, "Playback", fn)
            if os.path.exists(dp):
                target_owners.setdefault(dp, []).append((pname, song, kind))

    for dst_p, owners in sorted(target_owners.items()):
        # Deduplicate owners by song
        songs_set = {o[1] for o in owners}
        if len(songs_set) > 1:
            # Shared template file (e.g. 28_10_1/Playback/pb-other.wav = Alice Deejay); skip clobbering
            continue
        pname, song, kind = owners[0]
        if flt and (flt not in pname and flt not in song):
            continue
        if not os.path.exists(dst_p):
            continue
        src_dir = os.path.join(src_root, song, "auto-render")
        src_p = os.path.join(src_dir, kind)
        # Fallback if pb-other-keys.wav was merged into pb-other.wav
        if not os.path.exists(src_p) and kind == "pb-other-keys.wav":
            src_p = os.path.join(src_dir, "pb-other.wav")
        if not os.path.exists(src_p):
            continue
        # Only sync pb-* stems in <concert>/Playback/ unless click/cues length changed (or specific song filtered)
        if kind in ("click.wav", "cues.wav") and not flt and os.path.getsize(src_p) == os.path.getsize(dst_p):
            pb_skipped += 1
            continue
        rel_dst = os.path.relpath(dst_p, rig_root)
        if filecmp.cmp(src_p, dst_p, shallow=False):
            pb_skipped += 1
        else:
            print(f"  ↑ {rel_dst:50s} ← {song}/auto-render/{os.path.basename(src_p)}")
            if apply_flag:
                shutil.copy2(src_p, dst_p)
            pb_copied += 1

print(f"concert/Playback: changed: {pb_copied}   identical: {pb_skipped}")
PYEOF

if [ $APPLY -eq 1 ] && [ -n "$COMMIT_MSG" ]; then
  echo
  echo "=== committing in $RIG_ROOT (no push) ==="
  git -C "$RIG_ROOT" add -A "cherry-daddies-setlist-2026-06-16" "$RIG_ROOT"/*.concert/Playback
  git -C "$RIG_ROOT" commit -m "$COMMIT_MSG" || echo "(nothing to commit)"
  echo "Push when ready:  git -C \"$RIG_ROOT\" push"
elif [ $APPLY -eq 1 ]; then
  echo
  echo "Files copied. Review:  git -C \"$RIG_ROOT\" status"
else
  echo
  echo "Dry-run only. Re-run with --apply to copy."
fi
