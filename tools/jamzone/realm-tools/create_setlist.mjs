import Realm from "realm";
const r=await Realm.open({path:process.argv[2]});
const id=parseInt(process.argv[3],10), name=process.argv[4];
const songIds=JSON.parse(process.argv[5]);
r.write(()=>{
  r.create("Setlist",{id, name, songs: songIds.map(s=>({songId:s}))});
});
const sl=r.objectForPrimaryKey("Setlist",id);
console.log("created:",sl.name,"id",sl.id,"songs",[...sl.songs].map(s=>s.songId));
r.close(); process.exit(0);
