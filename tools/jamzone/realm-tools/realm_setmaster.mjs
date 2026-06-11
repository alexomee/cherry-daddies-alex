import Realm from "realm";
const r=await Realm.open({path:process.argv[2]});
const id=parseInt(process.argv[3],10), val=parseFloat(process.argv[4]);
r.write(()=>{ const j=r.objectForPrimaryKey("JamPreset",id);
  if(!j||!j.generalTrack){console.log("MISS",id);return;}
  j.generalTrack.volume=val; console.log("OK",id,"master=",val.toFixed(3)); });
r.close(); process.exit(0);
