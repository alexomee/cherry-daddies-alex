import Realm from "realm";
import fs from "fs";
const r = await Realm.open({ path: process.argv[2] });
const o={};
for(const j of [...r.objects("JamPreset")]){
  o[j.id]={ master: j.generalTrack?j.generalTrack.volume:1,
            muted: j.tracks.map(t=>t.isMuted), solo: j.tracks.map(t=>t.isSolo?1:0) };
}
fs.writeFileSync("/tmp/jz_mutes.json", JSON.stringify(o));
console.log("dumped", Object.keys(o).length, "presets");
r.close(); process.exit(0);
