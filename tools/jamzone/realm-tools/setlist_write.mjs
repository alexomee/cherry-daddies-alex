import Realm from "realm"; import fs from "fs";
const r=await Realm.open({path:process.argv[2]});
const id=parseInt(process.argv[3],10);
const order=JSON.parse(fs.readFileSync(process.argv[4],"utf8"));
const emb = r.schema.find(s=>s.name==="SetlistSong")?.embedded;
r.write(()=>{
  const sl=r.objectForPrimaryKey("Setlist",id);
  sl.songs = order.map(sid=>({songId:sid}));   // rebuild list in new order
});
const sl=r.objectForPrimaryKey("Setlist",id);
console.log("SetlistSong embedded:",emb,"| new length:",sl.songs.length);
console.log(JSON.stringify([...sl.songs].map(s=>s.songId)));
r.close(); process.exit(0);
