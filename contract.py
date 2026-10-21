# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import hashlib
import json
import re
from datetime import datetime, timezone


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise gl.vm.UserError('[EXPECTED] '+message)


def _canon(value) -> str:
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def _now() -> int:
    t=datetime.fromisoformat(gl.message_raw['datetime'].replace('Z','+00:00'))
    if t.tzinfo is None:
        t=t.replace(tzinfo=timezone.utc)
    delta=t.astimezone(timezone.utc)-datetime(1970,1,1,tzinfo=timezone.utc)
    return delta.days*86400+delta.seconds


def _id(value: str) -> None:
    _require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}',value) is not None,'invalid identifier')


def _source(url: str,digest: str) -> None:
    m=re.fullmatch(r'https://raw\.githubusercontent\.com/([A-Za-z0-9-]{1,39})/([A-Za-z0-9_.-]{1,100})/([0-9a-f]{40})/([A-Za-z0-9_.~/-]+)',url) if isinstance(url,str) and len(url)<=512 else None
    _require(m is not None,'commit-pinned public source required')
    owner,repo,commit,path=m.groups()
    _require(owner[0].isalnum() and owner[-1].isalnum() and '--' not in owner and repo not in ('.','..') and all(p not in ('','.','..') for p in path.split('/')),'commit-pinned unambiguous namespace required')
    _require(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest) is not None,'invalid SHA256')


def _pairs(pairs: list) -> dict:
    result={}
    for k,v in pairs:
        _require(k not in result,'duplicate JSON key');result[k]=v
    return result


def _constant(value: str):
    raise gl.vm.UserError('[EXPECTED] nonfinite JSON constant')


def _fetch(url: str,digest: str) -> dict:
    r=gl.nondet.web.get(url,headers={'Accept':'application/json'})
    if r.status!=200 or r.body is None or not 1<=len(r.body)<=16384 or hashlib.sha256(r.body).hexdigest()!=digest:
        raise gl.vm.UserError('[SOURCE] unavailable, oversized or byte digest mismatch')
    try:
        raw=json.loads(r.body.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=_constant)
    except (ValueError,UnicodeError,RecursionError):
        raise gl.vm.UserError('[SOURCE] invalid UTF-8 JSON')
    return _validate(raw)


def _validate(raw) -> dict:
    _require(isinstance(raw,dict) and set(raw)=={'version','capacity','max_bins','parcels','incompatible'} and type(raw['version']) is int and raw['version']==1,'manifest fields/version')
    cap=raw['capacity'];_require(isinstance(cap,dict) and set(cap)=={'weight','volume'},'capacity fields')
    _require(all(type(cap[k]) is int and 1<=cap[k]<=1000000 for k in ('weight','volume')),'positive exact capacity integers')
    _require(type(raw['max_bins']) is int and 1<=raw['max_bins']<=8,'max_bins integer1..8')
    parcels=raw['parcels'];_require(isinstance(parcels,list) and 1<=len(parcels)<=8,'1..8 parcels required')
    ids=set()
    for parcel in parcels:
        _require(isinstance(parcel,dict) and set(parcel)=={'id','weight','volume'},'parcel fields')
        ident=parcel['id'];_require(isinstance(ident,str) and re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,23}',ident) is not None and ident not in ids,'unique ASCII parcel ID');ids.add(ident)
        _require(all(type(parcel[k]) is int and 1<=parcel[k]<=1000000 for k in ('weight','volume')),'positive exact parcel integers')
    incompatible=raw['incompatible'];_require(isinstance(incompatible,list) and len(incompatible)<=28,'bounded incompatibilities')
    seen=set()
    for pair in incompatible:
        _require(isinstance(pair,list) and len(pair)==2 and all(isinstance(x,str) and x in ids for x in pair) and pair[0]!=pair[1],'known distinct parcel pair')
        normalized=tuple(sorted(pair));_require(normalized not in seen,'duplicate symmetric pair');seen.add(normalized)
    return {'version':1,'capacity':cap,'max_bins':raw['max_bins'],'parcels':sorted(parcels,key=lambda r:r['id']),'incompatible':[list(p) for p in sorted(seen)]}


def _derive(data: dict) -> dict:
    parcels=data['parcels'];cap=data['capacity'];blocked={tuple(p) for p in data['incompatible']}
    impossible={'decision':'INFEASIBLE','bin_count':0,'assignment':[],'bins':[]}
    if any(p['weight']>cap['weight'] or p['volume']>cap['volume'] for p in parcels):
        return impossible
    best_assignment=[];best_bins=[];bins=[];assignment=[]
    def search(index: int) -> None:
        nonlocal best_assignment,best_bins
        if index==len(parcels):
            if not best_bins or len(bins)<len(best_bins) or (len(bins)==len(best_bins) and tuple(assignment)<tuple(best_assignment)):
                best_assignment=list(assignment)
                best_bins=[{'index':i,'parcels':list(b['parcels']),'weight':b['weight'],'volume':b['volume']} for i,b in enumerate(bins)]
            return
        parcel=parcels[index]
        for i,container in enumerate(bins):
            if container['weight']+parcel['weight']>cap['weight'] or container['volume']+parcel['volume']>cap['volume'] or any(tuple(sorted((parcel['id'],other))) in blocked for other in container['parcels']):
                continue
            container['parcels'].append(parcel['id']);container['weight']+=parcel['weight'];container['volume']+=parcel['volume'];assignment.append(i)
            search(index+1)
            assignment.pop();container['parcels'].pop();container['weight']-=parcel['weight'];container['volume']-=parcel['volume']
        if len(bins)<data['max_bins'] and (not best_bins or len(bins)<len(best_bins)):
            # Only one next-numbered bin is introduced: no label permutations.
            assignment.append(len(bins));bins.append({'parcels':[parcel['id']],'weight':parcel['weight'],'volume':parcel['volume']})
            search(index+1)
            bins.pop();assignment.pop()
    search(0)
    if not best_bins:
        return impossible
    _require(len(best_assignment)==len(parcels) and sorted(p for b in best_bins for p in b['parcels'])==[p['id'] for p in parcels],'partition coverage invariant')
    return {'decision':'FEASIBLE','bin_count':len(best_bins),'assignment':best_assignment,'bins':best_bins}


def _capture(url: str,digest: str,binding: dict) -> dict:
    def leader() -> dict:
        data=_fetch(url,digest)
        return {'binding':binding,'source_sha256':digest,'data':data,'result':None if binding['operation']=='open' else _derive(data)}
    def validator(proposed: gl.vm.Result) -> bool:
        if not isinstance(proposed,gl.vm.Return):
            return False
        try:
            # Every validator fetches and recomputes the complete mathematical result.
            return _canon(leader())==_canon(proposed.calldata)
        except Exception:
            return False
    return gl.vm.run_nondet_unsafe(leader,validator)


class CargoNest(gl.Contract):
    loads: TreeMap[str,str]

    def __init__(self):
        pass

    def _get(self,ident: str) -> dict:
        _require(ident in self.loads,'unknown load')
        return json.loads(self.loads[ident])

    def _binding(self,d: dict,operation: str) -> dict:
        return {'protocol':'CargoNest-v1','chain_id':int(gl.message.chain_id),'contract':gl.message.contract_address.as_hex.lower(),'id':d['load_id'],'creator':d['creator'],'source_url':d['source_url'],'source_sha256':d['source_sha256'],'revision':d['revision'],'operation':operation,'observed_at':_now()}

    def _cas(self,d: dict,revision: int,creator: bool) -> None:
        if creator:
            _require(d['creator']==gl.message.sender_address.as_hex.lower(),'creator only')
        _require(type(revision) is int and revision==d['revision'],'stale revision')

    def _event(self,d: dict,operation: str) -> None:
        d['history'].append({'operation':operation,'revision':d['revision'],'observed_at':_now()})

    @gl.public.write
    def open_load(self,load_id: str,source_url: str,source_sha256: str) -> None:
        _id(load_id);_source(source_url,source_sha256)
        _require(load_id not in self.loads,'load_id already used')
        d={'load_id':load_id,'creator':gl.message.sender_address.as_hex.lower(),'source_url':source_url,'source_sha256':source_sha256,'status':'OPEN','revision':0,'opened_at':_now(),'derived_at':0,'confirmed_at':0,'revoked_at':0,'reason':'','history':[],'result':None,'certificate_id':''}
        packet=_capture(source_url,source_sha256,self._binding(d,'open'))
        d['data']=packet['data'];d['last_capture']=packet;self._event(d,'OPEN')
        self.loads[load_id]=_canon(d)

    @gl.public.write
    def pack_load(self,load_id: str,expected_revision: int) -> dict:
        d=self._get(load_id);self._cas(d,expected_revision,False)
        _require(d['status']=='OPEN','not open')
        packet=_capture(d['source_url'],d['source_sha256'],self._binding(d,'derive'))
        _require(_canon(packet['data'])==_canon(d['data']),'source snapshot mismatch')
        d['result']=packet['result'];d['last_capture']=packet;d['certificate_capture']=packet;d['certificate_id']=hashlib.sha256(_canon(packet).encode()).hexdigest()
        d['status']='PACKED';d['revision']=1;d['derived_at']=_now();self._event(d,'PACK')
        self.loads[load_id]=_canon(d)
        return d['result']

    @gl.public.write
    def confirm_load(self,load_id: str,expected_revision: int,certificate_id: str) -> None:
        d=self._get(load_id);self._cas(d,expected_revision,True)
        _require(d['status']=='PACKED','not ready to confirm')
        _require(isinstance(certificate_id,str) and certificate_id==d['certificate_id'],'wrong certificate')
        _require(d['result']['decision']=='FEASIBLE','FEASIBLE plan required')
        packet=_capture(d['source_url'],d['source_sha256'],self._binding(d,'confirm'))
        _require(_canon(packet['data'])==_canon(d['data']) and _canon(packet['result'])==_canon(d['result']),'source/result mismatch')
        d['last_capture']=packet;d['status']='CONFIRMED';d['revision']=2;d['confirmed_at']=_now();self._event(d,'CONFIRM')
        self.loads[load_id]=_canon(d)

    @gl.public.write
    def revoke_load(self,load_id: str,expected_revision: int,reason: str) -> None:
        d=self._get(load_id);self._cas(d,expected_revision,True)
        _require(d['status']!='REVOKED','already revoked')
        _require(isinstance(reason,str) and 1<=len(reason)<=160 and reason==reason.strip(),'bounded reason required')
        d['status']='REVOKED';d['revision']+=1;d['reason']=reason;d['revoked_at']=_now();self._event(d,'REVOKE')
        self.loads[load_id]=_canon(d)

    @gl.public.view
    def get_load(self,load_id: str) -> dict:
        return self._get(load_id)

    @gl.public.view
    def get_configuration(self) -> dict:
        return {'protocol':'CargoNest-v1','max_parcels':8,'max_complete_partitions':4140,'max_source_bytes':16384,'physical_dispatch_verified':False}
