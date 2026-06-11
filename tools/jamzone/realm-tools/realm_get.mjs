import Realm from "realm";
import fs from "fs";
const r = await Realm.open({ path: process.argv[2] });
const ids = process.argv[3].split(",").map(s=>parseInt(s,10));
const out=[];
for(const id of ids){
  const jp=r.objectForPrimaryKey("JamPreset",id);
  if(!jp){out.push(`${id}: MISSING`);continue;}
  out.push(`${id}: `+jp.tracks.map(t=>t.volume.toFixed(2)).join(","));
}
r.close();
fs.writeFileSync("/tmp/realm_get.txt", out.join("\n")+"\n");
console.log(out.join("\n"));
process.exit(0);
