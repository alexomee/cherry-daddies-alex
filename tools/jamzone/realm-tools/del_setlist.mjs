import Realm from "realm";
const r=await Realm.open({path:process.argv[2]});
const id=parseInt(process.argv[3],10);
const sl=r.objectForPrimaryKey("Setlist",id);
if(sl){ r.write(()=>r.delete(sl)); console.log("deleted test setlist",id); }
else console.log("test setlist",id,"already gone (app reconciled it away)");
r.close(); process.exit(0);
