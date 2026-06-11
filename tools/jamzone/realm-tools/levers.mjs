import Realm from "realm";
const r = await Realm.open({ path: process.argv[2] });
const ids=[12320,44331,52833,10091,11881,9348]; // jolene,getlucky,noroots,whatafeeling,calabria,believe
const tp=r.schema.find(s=>s.name==="TrackPreset");
for(const id of ids){
  const jp=r.objectForPrimaryKey("JamPreset",id);
  if(!jp){console.log(id,"missing");continue;}
  const gt=jp.generalTrack;
  console.log(`\n#${id}  level=${jp.level}  generalTrack=${gt?JSON.stringify({vol:gt.volume,mut:gt.isMuted,solo:gt.isSolo}):"null"}`);
  console.log("  isMuted per track:", jp.tracks.map(t=>t.isMuted).join(","));
  console.log("  isSolo  per track:", jp.tracks.map(t=>t.isSolo?1:0).join(","));
}
// distribution of level + generalTrack volume across all presets
const all=[...r.objects("JamPreset")];
const lv={}, gv={};
for(const j of all){ lv[j.level]=(lv[j.level]||0)+1; const v=j.generalTrack?j.generalTrack.volume:"none"; gv[v]=(gv[v]||0)+1;}
console.log("\nlevel value distribution:", JSON.stringify(lv));
console.log("generalTrack.volume distribution:", JSON.stringify(gv));
// isMuted value distribution
const im={};
for(const j of all) for(const t of j.tracks) im[t.isMuted]=(im[t.isMuted]||0)+1;
console.log("isMuted value distribution:", JSON.stringify(im));
r.close(); process.exit(0);
