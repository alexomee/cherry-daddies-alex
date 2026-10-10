#!/usr/bin/env python3
"""Setup mix.json for 27 Lefkara songs with proper cue formatting (one line per cue)
and automatic click: follow where resid > 8ms.
"""

import os, sys, json, glob

SONGS = os.path.expanduser("~/projects/cherry-daddies/music/songs")

def save_mix(folder, cues, click_mode=None, cat=None):
    p = os.path.join(SONGS, folder)
    mix_p = os.path.join(p, "mix.json")
    if os.path.exists(mix_p):
        data = json.load(open(mix_p))
    else:
        stems = sorted([os.path.basename(s)[:-4] for s in glob.glob(f"{p}/[0-9][0-9]_*.m4a")])
        drop = [s for s in stems if any(k in s.lower() for k in ["percussion", "conga", "bongo", "tambourine", "hand_clap", "clap", "timpani", "marimba"]) 
                and "kit" not in s.lower()]
        bass = [s for s in stems if "bass" in s.lower()]
        drums = [s for s in stems if "drum" in s.lower()]
        vox = [s for s in stems if "lead_vocal" in s.lower() or ("vocal" in s.lower() and "back" not in s.lower())]
        guitars = [s for s in stems if "guitar" in s.lower()]
        exclude = set(drop + bass + drums + vox)
        pb_other_stems = [s for s in stems if s not in exclude and "click" not in s.lower() and "count" not in s.lower()]
        
        players = {
            "steve": drums,
            "roma": bass,
            "tanya": vox
        }
        if guitars:
            players["alex"] = guitars
            
        data = {
            "pb-other": {"stems": pb_other_stems},
            "pb-bass": None,
            "pb-drums": {"stems": drums},
            "players": players
        }
        if cat:
            data["cat"] = cat
            
    if click_mode:
        data["click"] = click_mode
        
    data["cues"] = cues
    
    # Custom serializer to keep each cue on its own line
    # so jamzone_render write_cue_abs_times matches them
    cues_str = ",\n    ".join(json.dumps(c, ensure_ascii=False) for c in cues)
    
    # reconstruct json cleanly
    other_keys = {k: v for k, v in data.items() if k != "cues"}
    base_json = json.dumps(other_keys, indent=2, ensure_ascii=False)
    # insert cues before last closing brace
    last_brace = base_json.rfind("}")
    full_json = base_json[:last_brace].rstrip() + f',\n  "cues": [\n    {cues_str}\n  ]\n}}\n'
    
    with open(mix_p, "w", encoding="utf-8") as f:
        f.write(full_json)
    print(f"✓ Saved mix.json for {folder} ({len(cues)} cues)")

# -------------------------------------------------------------
# 1. 9 Existing songs with only 2 cues -> expand
# -------------------------------------------------------------

# 1. Bee Gees - Stayin' Alive
save_mix("Bee Gees - Stayin' Alive", [
    {"bar": 2, "text": "Stayin Alive all in"},
    {"bar": 7, "beat": 4, "text": "verse in"},
    {"bar": 27, "text": "main in ready go"},
    {"bar": 29, "text": "verse in ready go"},
    {"bar": 48, "text": "main in ready go"},
    {"bar": 50, "text": "bridge in ready go"},
    {"bar": 125, "text": "end in", "count": True}
])

# 3. Gloria Gaynor - I Will Survive
save_mix("Gloria Gaynor - I Will Survive", [
    {"bar": 2, "text": "I Will Survive playback in"},
    {"bar": 5, "text": "guitars in"},
    {"bar": 13, "text": "all in"},
    {"bar": 45, "text": "verse in ready go"},
    {"bar": 76, "text": "music stop"},
    {"bar": 78, "beat": 4, "text": "voice in ready go"},
    {"bar": 103, "text": "end in", "count": True}
])

# 4. Village People - Y.M.C.A.
save_mix("Village People - Y.M.C.A.", [
    {"bar": 3, "text": "YMCA all in"},
    {"bar": 9, "beat": 1, "text": "verse in"},
    {"bar": 111, "beat": 1, "text": "instrumental in ready go"},
    {"bar": 119, "beat": 1, "text": "chorus in ready go"},
    {"bar": 147, "text": "end in", "count": True}
])

# 5. Donna Summer - Hot Stuff
save_mix("Donna Summer - Hot Stuff", [
    {"bar": 2, "text": "Hot Stuff all in"},
    {"bar": 17, "beat": 4, "text": "verse in"},
    {"bar": 74, "text": "guitar solo ready go"},
    {"bar": 98, "text": "chorus in ready go"},
    {"bar": 160, "text": "end in", "count": True}
])

# 7. Ricchi e Poveri - Sarà perché ti amo
save_mix("Ricchi e Poveri - Sarà perché ti amo", [
    {"bar": 3, "text": "Ti amo all in ready go"},
    {"bar": 11, "text": "voice-only verse ready go"},
    {"bar": 17, "text": "kick in ready go"},
    {"bar": 19, "text": "all in ready go"},
    {"bar": 59, "text": "instrumental in ready go"},
    {"bar": 67, "text": "chorus in ready go"},
    {"bar": 91, "beat": 1, "text": "end fill in", "count": True}
])

# 11. Weather Girls - It's Raining Men
save_mix("Weather Girls - It's Raining Men", [
    {"bar": 1, "text": "It's Raining Men playback in"},
    {"bar": 3, "text": "all in"},
    {"bar": 19, "text": "main in ready go"},
    {"bar": 26, "beat": 4, "text": "verse in"},
    {"bar": 91, "text": "break in ready go"},
    {"bar": 109, "text": "bridge in ready go"},
    {"bar": 185, "text": "end in", "count": True}
])

# 12. Flashdance (Michael Sembello) - Maniac
save_mix("Flashdance (Michael Sembello) - Maniac", [
    {"bar": 3, "text": "Maniac drums in"},
    {"bar": 11, "text": "main in ready go"},
    {"bar": 18, "beat": 4, "text": "verse in"},
    {"bar": 101, "text": "bridge in"},
    {"bar": 117, "text": "guitar solo ready go"},
    {"bar": 133, "text": "prechorus in"},
    {"bar": 140, "beat": 4, "text": "chorus in ready go"},
    {"bar": 171, "text": "end in", "count": True}
])

# 13. Eurythmics - Sweet Dreams (Are Made of This)
save_mix("Eurythmics - Sweet Dreams (Are Made of This)", [
    {"bar": 3, "text": "Sweet Dreams playback in"},
    {"bar": 7, "text": "chorus in"},
    {"bar": 15, "text": "verse in"},
    {"bar": 51, "text": "break in ready go"},
    {"bar": 59, "text": "verse in ready go"},
    {"bar": 113, "text": "end in", "count": True}
])

# 17. Modern Talking - You're My Heart, You're My Soul (Mix '98)
save_mix("Modern Talking - You're My Heart, You're My Soul (Mix '98)", [
    {"bar": 2, "text": "You're My Heart all in"},
    {"bar": 10, "beat": 3, "text": "verse in"},
    {"bar": 44, "beat": 3, "text": "melody in ready go"},
    {"bar": 61, "text": "verse in ready go"},
    {"bar": 111, "text": "end fill in", "count": True}
])

# -------------------------------------------------------------
# 2. 12 New songs -> configure mix.json & cues
# -------------------------------------------------------------

# 6. ABBA - Gimme! Gimme! Gimme!
save_mix("ABBA - Gimme! Gimme! Gimme! (A Man After Midnight)", [
    {"bar": 2, "text": "Gimme Gimme Gimme playback in"},
    {"bar": 11, "text": "drums in"},
    {"bar": 19, "beat": 4, "text": "verse in"},
    {"bar": 88, "text": "main in ready go"},
    {"bar": 118, "text": "chorus in ready go"},
    {"bar": 134, "text": "end in", "count": True}
], click_mode="follow", cat="cat_9159")

# 8. Joan Jett - I Love Rock 'n' Roll
save_mix("Joan Jett - I Love Rock 'n' Roll", [
    {"bar": 2, "text": "I Love Rock n Roll guitar in"},
    {"bar": 7, "beat": 3, "text": "verse in"},
    {"bar": 18, "text": "chorus in"},
    {"bar": 40, "beat": 2, "text": "guitar solo ready go"},
    {"bar": 51, "text": "bridge in ready go"},
    {"bar": 55, "text": "end in", "count": True}
], click_mode="follow", cat="cat_9455")

# 9. Al Bano & Romina Power - Felicità
save_mix("Al Bano & Romina Power - Felicità", [
    {"bar": 2, "text": "Felicita all in"},
    {"bar": 13, "beat": 4, "text": "verse in"},
    {"bar": 29, "beat": 3, "text": "chorus in"},
    {"bar": 45, "beat": 3, "text": "main in ready go"},
    {"bar": 47, "beat": 3, "text": "verse in ready go"},
    {"bar": 79, "text": "end in", "count": True}
], cat="cat_16687")

# 10. Ricchi e Poveri - Mamma María
save_mix("Ricchi e Poveri - Mamma María", [
    {"bar": 3, "text": "Mamma Maria all in"},
    {"bar": 7, "text": "verse in"},
    {"bar": 55, "text": "instrumental in ready go"},
    {"bar": 67, "text": "verse in ready go"},
    {"bar": 83, "text": "keep going"},
    {"bar": 107, "text": "end in", "count": True}
], cat="cat_82836")

# 14. Cyndi Lauper - Girls Just Want to Have Fun
save_mix("Cyndi Lauper - Girls Just Want to Have Fun", [
    {"bar": 3, "text": "Girls Just Want to Have Fun all in"},
    {"bar": 11, "beat": 2, "text": "verse in"},
    {"bar": 20, "text": "break in ready go"},
    {"bar": 24, "text": "verse in ready go"},
    {"bar": 45, "beat": 4, "text": "main in ready go"},
    {"bar": 53, "beat": 4, "text": "verse in ready go"},
    {"bar": 75, "beat": 4, "text": "end in", "count": True}
], cat="cat_8231")

# 15. Flashdance (Irene Cara) - What a Feeling
save_mix("Flashdance (Irene Cara) - What a Feeling", [
    {"bar": 2, "text": "What a Feeling guitars in"},
    {"bar": 6, "text": "verse in"},
    {"bar": 20, "text": "all in"},
    {"bar": 48, "text": "solo in ready go"},
    {"bar": 55, "beat": 4, "text": "vocal in"},
    {"bar": 80, "text": "bridge in"},
    {"bar": 88, "text": "chorus variation ready go"},
    {"bar": 96, "text": "outro in ready go"},
    {"bar": 104, "text": "keep going"},
    {"bar": 114, "text": "end in", "count": True}
], click_mode="follow", cat="cat_10091")

# 18. Footloose (1984 film) - Holding Out for a Hero
save_mix("Footloose (1984 film) - Holding Out for a Hero", [
    {"bar": 3, "text": "Holding Out for a Hero drum-base in"},
    {"bar": 23, "text": "verse in"},
    {"bar": 38, "beat": 3, "text": "chorus in"},
    {"bar": 55, "text": "intro in"},
    {"bar": 63, "text": "verse in"},
    {"bar": 101, "text": "bridge in"},
    {"bar": 117, "text": "voice in"},
    {"bar": 137, "beat": 4, "text": "chorus in"},
    {"bar": 153, "text": "keep going"},
    {"bar": 170, "text": "outro in ready go"},
    {"bar": 194, "text": "keep going"},
    {"bar": 206, "text": "end in", "count": True}
], click_mode="follow", cat="cat_13868")

# 22. Whitney Houston - I Wanna Dance with Somebody (Who Loves Me)
save_mix("Whitney Houston - I Wanna Dance with Somebody (Who Loves Me)", [
    {"bar": 2, "text": "I Wanna Dance all in"},
    {"bar": 4, "beat": 4, "text": "vocal in"},
    {"bar": 18, "text": "verse in"},
    {"bar": 113, "beat": 2, "text": "break in ready go"},
    {"bar": 121, "beat": 2, "text": "bridge in ready go"},
    {"bar": 137, "beat": 2, "text": "end in", "count": True}
], click_mode="follow", cat="cat_5468")

# 23. Tina Turner - The Best
save_mix("Tina Turner - The Best", [
    {"bar": 2, "text": "The Best all in"},
    {"bar": 5, "beat": 4, "text": "verse in"},
    {"bar": 30, "text": "chorus in"},
    {"bar": 82, "text": "sax solo ready go"},
    {"bar": 90, "text": "chorus in ready go"},
    {"bar": 98, "text": "end in", "count": True}
], click_mode="follow", cat="cat_5519")

# 24. Boney M. - Sunny
save_mix("Boney M. - Sunny", [
    {"bar": 2, "text": "Sunny, all in ready go"},
    {"bar": 10, "text": "verse in"},
    {"bar": 42, "text": "modulation in"},
    {"bar": 58, "text": "instrumental in"},
    {"bar": 74, "text": "modulation in"},
    {"bar": 88, "text": "outro in"},
    {"bar": 96, "text": "end in", "count": True}
], cat="cat_5568")

# 25. ABBA - Money, Money, Money
save_mix("ABBA - Money, Money, Money", [
    {"bar": 2, "text": "Money Money Money playback in"},
    {"bar": 6, "text": "drums in"},
    {"bar": 7, "beat": 4, "text": "verse in"},
    {"bar": 25, "beat": 2, "text": "chorus in"},
    {"bar": 90, "text": "end in", "count": True}
], click_mode="follow", cat="cat_5459")

# 27. Haddaway - What Is Love
save_mix("Haddaway - What Is Love", [
    {"bar": 1, "text": "What Is Love playback in"},
    {"bar": 5, "text": "all in"},
    {"bar": 22, "beat": 2, "text": "verse in"},
    {"bar": 38, "beat": 2, "text": "main in ready go"},
    {"bar": 46, "beat": 2, "text": "chorus in ready go"},
    {"bar": 93, "beat": 4, "text": "break in ready go"},
    {"bar": 97, "beat": 4, "text": "bridge in ready go"},
    {"bar": 129, "beat": 3, "text": "end in", "count": True}
], cat="cat_19903")
