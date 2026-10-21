import {expect,it} from 'vitest';
import {openArgs,binRows,canConfirm} from '../src/domain';
const creator='0x1111111111111111111111111111111111111111';
const record={load_id:'load',creator,status:'PACKED',revision:1,certificate_id:'b'.repeat(64),data:{version:1,capacity:{weight:10,volume:10},max_bins:2,parcels:[{id:'a',weight:6,volume:3},{id:'b',weight:4,volume:7}],incompatible:[] as string[][]},result:{decision:'FEASIBLE',bin_count:1,assignment:[0,0],bins:[{index:0,parcels:['a','b'],weight:10,volume:10}]}};
it('shows actual chain container members and both capacity sums',()=>{expect(binRows(record)).toEqual(record.result.bins);});
it('never turns open or infeasible output into a shipment plan',()=>{expect(binRows({...record,status:'OPEN',result:null})).toEqual([]);expect(binRows({...record,result:{decision:'INFEASIBLE',bin_count:0,assignment:[],bins:[]}})).toEqual([]);});
it('rejects missing/duplicate parcels or impossible totals',()=>{expect(()=>binRows({...record,result:{...record.result,bins:[{index:0,parcels:['a','a'],weight:10,volume:10}]}})).toThrow();expect(()=>binRows({...record,result:{...record.result,bins:[{index:0,parcels:['a','b'],weight:1,volume:10}]}})).toThrow();});
it('rejects a conflict or mismatched assignment in purported chain output',()=>{expect(()=>binRows({...record,data:{...record.data,incompatible:[['a','b']]}})).toThrow();expect(()=>binRows({...record,result:{...record.result,assignment:[0,1]}})).toThrow();});
it('allows creator confirmation only for a complete current feasible result',()=>{expect(canConfirm(record,creator)).toBe(true);expect(canConfirm({...record,status:'REVOKED'},creator)).toBe(false);expect(canConfirm({...record,certificate_id:''},creator)).toBe(false);expect(canConfirm(record,'0x2222222222222222222222222222222222222222')).toBe(false);});
it.each(['.','..','%2e'])('rejects ambiguous repository %s',repo=>{expect(()=>openArgs('s','https://raw.githubusercontent.com/example/'+repo+'/'+'a'.repeat(40)+'/input.json','b'.repeat(64))).toThrow('commit-pinned');});
it.each(['.github','repo.name','_repo'])('preserves valid repository %s',repo=>{const url='https://raw.githubusercontent.com/example/'+repo+'/'+'a'.repeat(40)+'/input.json';expect(openArgs('s',url,'b'.repeat(64))).toEqual(['s',url,'b'.repeat(64)]);});

it("blocks confirmation after visible record ID changes without a fresh read",()=>{expect(canConfirm(record,creator,"another-record")).toBe(false);});
