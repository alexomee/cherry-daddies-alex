import Realm from "realm";
const r=await Realm.open({path:process.argv[2]});
console.log("ALL CLASSES:");
for(const s of r.schema) console.log(` ${s.name}${s.primaryKey?` (pk=${s.primaryKey})`:""}${s.embedded?" [emb]":""}: ${Object.keys(s.properties).join(", ")}`);
// anything sync/operation/pending/dirty-ish
console.log("\nSYNC-ish classes:");
for(const s of r.schema) if(/sync|pending|operation|mutation|dirty|upload|queue|change|local/i.test(s.name+Object.keys(s.properties).join())) console.log("  ",s.name, Object.keys(s.properties));
// Setlist id range (to understand id assignment) + any with negative/odd ids
const sls=[...r.objects("Setlist")].map(s=>s.id).sort((a,b)=>a-b);
console.log("\nSetlist ids:", sls.join(","));
r.close(); process.exit(0);
