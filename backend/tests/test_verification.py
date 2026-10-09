import json
from app.config import ROOT
from app.integrations import Tools
from app.ai import AI
from app.schemas import Attendee
from app.verify import verify

def fixture_records(eid):
    tools=Tools('test');calendar=tools.call('calendar',eid)
    attendees=[Attendee(name=a['displayName'],email=a['email'],event_id=eid,source_id=cal['id']+':'+a['email'],source_type='calendar').model_dump() for cal in calendar for a in cal['attendees']]
    attendees += [a.model_dump() for a in AI().extract(tools.call('gmail',eid),eid)]
    return attendees,tools.call('web',eid)

def test_controlled_edge_cases_match_expected():
    expected=json.loads((ROOT/'data/fixtures/expected.json').read_text())
    for eid,categories in expected.items():
        a,d=fixture_records(eid);rows=verify(a,d,eid)
        for status,keys in categories.items():
            actual=sorted(r['record']['email'] or r['record']['name'] for r in rows if r['status']==status)
            assert actual==sorted(keys)

def test_duplicate_is_not_exportable():
    a,d=fixture_records('EVT-101');row=next(r for r in verify(a,d,'EVT-101') if r['record']['email']=='ben@example.org')
    assert row['status']=='review_required';assert 'Duplicate registration messages' in row['reasons']
    assert len(row['evidence'])==4

def test_unavailable_source_prevents_verification():
    a,d=fixture_records('EVT-102');rows=verify(a,d,'EVT-102',['calendar'])
    assert all(r['status']!='verified' for r in rows)

def test_missing_directory_is_unverified():
    a,d=fixture_records('EVT-102');assert all(r['status']=='unverified' for r in verify(a,[],'EVT-102'))

def test_normalization_preserves_source_ids():
    a,d=fixture_records('EVT-102')
    for r in a:r['email']='  '+r['email'].upper()+'  ';r['name']='  '+r['name']+'  '
    rows=verify(a,d,'EVT-102');assert all(r['status']=='verified' for r in rows)
    assert rows[0]['evidence'][0]['source_id']==a[1]['source_id'] or rows[0]['evidence'][0]['source_id']==a[3]['source_id']
