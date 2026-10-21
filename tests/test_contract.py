"""Real GenVM execution, fictional HTTP bytes; literal partition expectations."""
import hashlib
import json
from pathlib import Path
import re
import pytest

ROOT=Path(__file__).parents[1]
META=json.loads((ROOT/'fixtures/source.json').read_text())
BODY=(ROOT/'fixtures/input.json').read_bytes().decode('utf-8')


def deploy(vm,build):
    vm.warp('2026-10-21T00:00:00Z');c=build(str(ROOT/'contract.py'),sdk_version='v0.2.12')
    assert hasattr(c,'open_load'),'CargoNest API NOT_IMPLEMENTED'
    return c


def opened(vm,c,body=BODY,ident='load'):
    vm.clear_mocks()
    vm.mock_web(re.escape(META['test_url']),{'status':200,'body':body})
    c.open_load(ident,META['test_url'],hashlib.sha256(body.encode()).hexdigest())


def packed(vm,c,body=BODY):
    opened(vm,c,body);return c.pack_load('load',0)


def tiny(n=3,weight=1,volume=1,capacity=2,max_bins=8):
    return {'version':1,'capacity':{'weight':capacity,'volume':capacity},'max_bins':max_bins,'parcels':[{'id':chr(97+i),'weight':weight,'volume':volume} for i in range(n)],'incompatible':[]}


def test_literal_minimum_partition_and_confirmed_manifest(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);r=packed(direct_vm,c)
    assert r=={'decision':'FEASIBLE','bin_count':2,'assignment':[0,0,1,1],'bins':[{'index':0,'parcels':['a','b'],'weight':10,'volume':10},{'index':1,'parcels':['c','d'],'weight':10,'volume':10}]}
    assert direct_vm.run_validator() is True
    d=c.get_load('load');c.confirm_load('load',1,d['certificate_id'])
    assert c.get_load('load')['status']=='CONFIRMED' and c.get_load('load')['revision']==2
    assert direct_vm.run_validator() is True


def test_lexicographic_restricted_growth_tie_and_permutation(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);s=tiny();r=packed(direct_vm,c,json.dumps(s))
    assert r['bin_count']==2 and r['assignment']==[0,0,1]
    s['parcels'].reverse();opened(direct_vm,c,json.dumps(s),'reverse')
    assert c.pack_load('reverse',0)==r


def test_volume_constraint_and_pair_exclusion_are_independent(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);s=tiny(volume=6,capacity=10)
    assert packed(direct_vm,c,json.dumps(s))['bin_count']==3
    s=tiny(n=2,capacity=10);s['incompatible']=[['b','a']];opened(direct_vm,c,json.dumps(s),'pair')
    assert c.pack_load('pair',0)['assignment']==[0,1]


@pytest.mark.parametrize('kind',['max_bins','oversize'])
def test_infeasible_is_not_confirmable_or_a_plan(direct_vm,direct_deploy,kind):
    c=deploy(direct_vm,direct_deploy);s=tiny(n=2,weight=6,capacity=10,max_bins=1)
    if kind=='oversize':s['parcels'][0]['weight']=11
    assert packed(direct_vm,c,json.dumps(s))=={'decision':'INFEASIBLE','bin_count':0,'assignment':[],'bins':[]}
    d=c.get_load('load')
    with direct_vm.expect_revert('FEASIBLE'):c.confirm_load('load',1,d['certificate_id'])
    assert c.get_load('load')['status']=='PACKED'


def test_eight_parcels_positive_bound_and_one_bin(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);r=packed(direct_vm,c,json.dumps(tiny(n=8,capacity=8,max_bins=1)))
    assert r['assignment']==[0]*8 and r['bins'][0]['parcels']==list('abcdefgh')


@pytest.mark.parametrize('kind',['zero','bool','float','too_large','bad_id','duplicate_id','unknown_pair','self_pair','duplicate_pair','extra','nine','version_bool','empty','max_bins_bool','capacity_bool','capacity_zero'])
def test_strict_manifest_bounds_and_pair_shapes(direct_vm,direct_deploy,kind):
    c=deploy(direct_vm,direct_deploy);s=tiny()
    if kind=='zero':s['parcels'][0]['weight']=0
    if kind=='bool':s['parcels'][0]['weight']=True
    if kind=='float':s['parcels'][0]['volume']=1.0
    if kind=='too_large':s['parcels'][0]['weight']=1000001
    if kind=='bad_id':s['parcels'][0]['id']='a|b'
    if kind=='duplicate_id':s['parcels'][1]['id']='a'
    if kind=='unknown_pair':s['incompatible']=[['a','z']]
    if kind=='self_pair':s['incompatible']=[['a','a']]
    if kind=='duplicate_pair':s['incompatible']=[['a','b'],['b','a']]
    if kind=='extra':s['parcels'][0]['address']='not allowed'
    if kind=='nine':s=tiny(n=9)
    if kind=='version_bool':s['version']=True
    if kind=='empty':s['parcels']=[]
    if kind=='max_bins_bool':s['max_bins']=True
    if kind=='capacity_bool':s['capacity']['volume']=True
    if kind=='capacity_zero':s['capacity']['volume']=0
    with direct_vm.expect_revert():opened(direct_vm,c,json.dumps(s))


@pytest.mark.parametrize('kind',['duplicate','nan','malformed','oversized'])
def test_json_and_byte_bounds(direct_vm,direct_deploy,kind):
    c=deploy(direct_vm,direct_deploy);body=BODY
    if kind=='duplicate':body=body.replace('"version": 1','"version": 1,"version": 1')
    if kind=='nan':body=body.replace('"weight": 6','"weight": NaN')
    if kind=='malformed':body='{'
    if kind=='oversized':body+=' '*17000
    with direct_vm.expect_revert():opened(direct_vm,c,body)


@pytest.mark.parametrize('repo',['.','..','%2e','repo?bad'])
def test_bad_namespace_fails_before_fetch(direct_vm,direct_deploy,repo):
    c=deploy(direct_vm,direct_deploy)
    with direct_vm.expect_revert('commit-pinned'):c.open_load('bad','https://raw.githubusercontent.com/example/'+repo+'/'+'a'*40+'/input.json','b'*64)


@pytest.mark.parametrize('field',['assignment','weight','count','binding'])
def test_validator_recomputes_global_optimum_and_all_evidence(direct_vm,direct_deploy,field):
    c=deploy(direct_vm,direct_deploy);packed(direct_vm,c);d=c.get_load('load')['last_capture']
    if field=='assignment':d['result']['assignment']=[0,1,0,1]
    if field=='weight':d['result']['bins'][0]['weight']=0
    if field=='count':d['result']['bin_count']=1
    if field=='binding':d['binding']['id']='another'
    assert direct_vm.run_validator(leader_result=d) is False


def test_fresh_source_drift_and_owner_cas_cert_terminal(direct_vm,direct_deploy):
    from gltest.direct import create_address
    c=deploy(direct_vm,direct_deploy);opened(direct_vm,c)
    with direct_vm.prank(create_address('packer')):c.pack_load('load',0)
    d=c.get_load('load')
    with direct_vm.prank(create_address('other')):
        with direct_vm.expect_revert('creator only'):c.confirm_load('load',1,d['certificate_id'])
        with direct_vm.expect_revert('creator only'):c.revoke_load('load',1,'not mine')
    with direct_vm.expect_revert('revision'):c.confirm_load('load',0,d['certificate_id'])
    with direct_vm.expect_revert('certificate'):c.confirm_load('load',1,'00'*32)
    opened(direct_vm,c,ident='other');c.pack_load('other',0)
    assert c.get_load('other')['certificate_id']!=d['certificate_id']
    with direct_vm.expect_revert('certificate'):c.confirm_load('other',1,d['certificate_id'])
    c.confirm_load('load',1,d['certificate_id'])
    with direct_vm.expect_revert():c.confirm_load('load',2,d['certificate_id'])
    direct_vm.clear_mocks();c.revoke_load('load',2,'Retired planning input.')
    assert c.get_load('load')['status']=='REVOKED' and len(c.get_load('load')['history'])==4
    with direct_vm.expect_revert():c.revoke_load('load',3,'Again')
    with direct_vm.expect_revert():c.pack_load('load',3)
    with direct_vm.expect_revert():opened(direct_vm,c)


def test_confirm_refetch_failure_preserves_exact_state(direct_vm,direct_deploy):
    c=deploy(direct_vm,direct_deploy);packed(direct_vm,c);d=c.get_load('load')
    direct_vm.clear_mocks();direct_vm.mock_web(re.escape(META['test_url']),{'status':200,'body':'changed'})
    assert direct_vm.run_validator() is False
    with direct_vm.expect_revert('SOURCE'):c.confirm_load('load',1,d['certificate_id'])
    assert c.get_load('load')==d
    c.revoke_load('load',1,'Source unavailable.')


def test_fixture_exact_bytes_match_declared_publication_metadata():
    body=(ROOT/'fixtures/input.json').read_bytes()
    assert len(body)==META['bytes']
    assert hashlib.sha256(body).hexdigest()==META['sha256']
    assert META['public_url'] is None and META['live_source_verified'] is False
