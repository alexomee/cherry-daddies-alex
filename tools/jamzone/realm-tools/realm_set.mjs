// realm_set.mjs <realmPath> <editsJsonPath>
// edits = { "<songId>": { "<idx>": <volume double>, ... }, ... }
import Realm from "realm";
import fs from "fs";
const [,, realmPath, editsPath] = process.argv;
const edits = JSON.parse(fs.readFileSync(editsPath,"utf8"));
const out=[];
try{
  const r = await Realm.open({ path: realmPath });
  r.write(()=>{
    for(const [sid,map] of Object.entries(edits)){
      const jp = r.objectForPrimaryKey("JamPreset", parseInt(sid,10));
      if(!jp){ out.push(`MISS songId ${sid} (no JamPreset)`); continue; }
      for(const t of jp.tracks){
        if(map[String(t.idx)]!==undefined) t.volume = map[String(t.idx)];
      }
      out.push(`OK ${sid}: ${jp.tracks.map(t=>t.volume.toFixed(2)).join(",")}`);
    }
  });
  r.close();
}catch(e){ out.push("ERROR: "+e.message+"\n"+e.stack); }
fs.writeFileSync("/tmp/realm_set_result.txt", out.join("\n")+"\n");
console.log(out.join("\n"));
process.exit(0);
