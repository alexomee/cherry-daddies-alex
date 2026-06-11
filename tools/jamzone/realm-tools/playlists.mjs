import Realm from "realm";
const r=await Realm.open({path:process.argv[2]});
// list classes whose name or props hint at playlists/setlists
console.log("=== all classes ===");
for(const s of r.schema){
  const props=Object.keys(s.properties).join(",");
  if(/playlist|setlist|set|songs|order/i.test(s.name+props))
    console.log(`${s.name}${s.primaryKey?` (pk=${s.primaryKey})`:""}: ${props}`);
}
// find the playlist object class & dump matching ones
for(const s of r.schema){
  if(/playlist|setlist/i.test(s.name)){
    console.log(`\n=== objects of ${s.name} ===`);
    for(const o of r.objects(s.name)){
      const name=o.name||o.title||o.label||"?";
      const songsProp=Object.keys(s.properties).find(k=>/song/i.test(k));
      let n="?"; try{ n=o[songsProp]?.length }catch{}
      console.log(`  "${name}"  ${songsProp}[${n}]  pk=${s.primaryKey?o[s.primaryKey]:""}`);
    }
  }
}
r.close(); process.exit(0);
