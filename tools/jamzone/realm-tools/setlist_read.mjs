import Realm from "realm"; import fs from "fs";
const r=await Realm.open({path:process.argv[2]});
const sl=r.objectForPrimaryKey("Setlist",parseInt(process.argv[3],10));
const ids=[...sl.songs].map(s=>s.songId);
fs.writeFileSync("/tmp/jz_setlist.json", JSON.stringify({id:sl.id,name:sl.name,ids}));
console.log(JSON.stringify(ids));
r.close(); process.exit(0);
