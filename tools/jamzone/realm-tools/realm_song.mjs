import Realm from "realm"; import fs from "fs";
const r=await Realm.open({path:process.argv[2]});
const j=r.objectForPrimaryKey("JamPreset",parseInt(process.argv[3],10));
const out = j ? {id:j.id, master:(j.generalTrack?j.generalTrack.volume:1),
  tracks:j.tracks.map(t=>({idx:t.idx,volume:t.volume,isMuted:t.isMuted,isSolo:!!t.isSolo}))} : null;
fs.writeFileSync("/tmp/jz_song.json", JSON.stringify(out));
console.log(JSON.stringify(out)); r.close(); process.exit(0);
