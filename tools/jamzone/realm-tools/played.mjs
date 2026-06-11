import Realm from "realm";
const r = await Realm.open({ path: process.argv[2] });
const ps = [...r.objects("PlayedSong")].map(p=>({id:p.playedId,date:p.date}));
ps.sort((a,b)=> (b.date?.getTime?.()||0)-(a.date?.getTime?.()||0));
console.log("most-recent PlayedSong ids (newest first):");
console.log(ps.slice(0,25).map(p=>p.id).join(","));
r.close(); process.exit(0);
