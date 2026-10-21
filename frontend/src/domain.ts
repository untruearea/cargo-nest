export interface Parcel{id:string;weight:number;volume:number}
export interface Container{index:number;parcels:string[];weight:number;volume:number}
export interface LoadRecord{load_id:string;creator:string;status:string;revision:number;certificate_id:string;data:{version:number;capacity:{weight:number;volume:number};max_bins:number;parcels:Parcel[];incompatible:string[][]};result:{decision:string;bin_count:number;assignment:number[];bins:Container[]}|null}
export function openArgs(id:string,url:string,sha:string):[string,string,string]{
 if(!/^[A-Za-z0-9_-]{1,64}$/.test(id))throw Error('Use a unique 1–64 character ASCII ID.');
 const m=url.match(/^https:\/\/raw\.githubusercontent\.com\/([A-Za-z0-9-]{1,39})\/([A-Za-z0-9_.-]{1,100})\/([0-9a-f]{40})\/([A-Za-z0-9_.~/-]+)$/);
 if(!m||m[0]!==url||url.length>512||!/[A-Za-z0-9]/.test(m[1][0])||!/[A-Za-z0-9]/.test(m[1].at(-1)!)||m[1].includes('--')||url.split('/').slice(3).some(s=>!s||s==='.'||s==='..'))throw Error('Use an unambiguous public commit-pinned GitHub URL.');
 if(!/^[0-9a-f]{64}$/.test(sha))throw Error('Enter the exact lowercase byte SHA256.');return [id,url,sha];
}
export function binRows(r:LoadRecord):Container[]{
 if(r.status==='OPEN'||!r.result||r.result.decision==='INFEASIBLE')return [];
 const p=r.result,parcels=[...r.data.parcels].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0),byId=new Map(parcels.map(x=>[x.id,x]));
 if(p.decision!=='FEASIBLE'||!p.bins.length||p.bin_count!==p.bins.length||p.bin_count>r.data.max_bins||p.assignment.length!==parcels.length)throw Error('Inconsistent partition record.');
 const seen=new Set<string>();
 for(const [i,b] of p.bins.entries()){
  if(b.index!==i||!b.parcels.length)throw Error('Invalid bin index or empty bin.');let weight=0,volume=0;
  for(const id of b.parcels){const parcel=byId.get(id),index=parcels.findIndex(x=>x.id===id);if(!parcel||seen.has(id)||p.assignment[index]!==i)throw Error('Duplicate/missing parcel assignment.');seen.add(id);weight+=parcel.weight;volume+=parcel.volume;}
  if(weight!==b.weight||volume!==b.volume||weight>r.data.capacity.weight||volume>r.data.capacity.volume)throw Error('Capacity totals mismatch.');
  if(r.data.incompatible.some(([a,c])=>b.parcels.includes(a)&&b.parcels.includes(c)))throw Error('Incompatible parcels share a bin.');
 }
 if(seen.size!==parcels.length)throw Error('Incomplete partition coverage.');return p.bins;
}
export function canConfirm(r:LoadRecord,account:string,visibleId:string=r.load_id):boolean{try{return visibleId===r.load_id&&r.status==='PACKED'&&r.revision===1&&r.creator.toLowerCase()===account.toLowerCase()&&/^[0-9a-f]{64}$/.test(r.certificate_id)&&r.result?.decision==='FEASIBLE'&&binRows(r).length>0;}catch{return false;}}
