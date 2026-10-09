"""Generate reproducible, wholly fictional assessment data."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def save(path,data): (root/path).write_text(json.dumps(data,indent=2)+'\n')
events=[]
for number,name,day,venue in [(101,'Operations Leadership Forum',15,'Sandton Convention Studio'),(102,'Community Systems Workshop',22,'Rosebank Learning Hub'),(103,'Partner Collaboration Summit',29,'Cape Town Exchange')]:
    events.append(dict(record_id=f'event-{number}',event_id=f'EVT-{number}',name=name,date=f'2026-11-{day}',start_time='09:00',end_time='16:00',timezone='Africa/Johannesburg',venue=venue,capacity=60,registration_deadline=f'2026-11-{day-3}T17:00:00+02:00'))
policies=[dict(record_id='policy-001',event_id=None,title='Registration authority',rule='The published participant directory is authoritative for participant identity, organization, active status and event eligibility. Invitations alone do not confirm registration.',authority='Event Operations'),dict(record_id='policy-002',event_id=None,title='Refunds',rule='Cancellation at least seven days before the event qualifies for a full refund. Later cancellations require staff review.',authority='Finance'),dict(record_id='policy-003',event_id='EVT-101',title='Check-in schedule',rule='Check-in opens at 08:30. The programme starts at 09:00. Registration closes on 12 November 2026 at 17:00 SAST.',authority='Event Operations'),dict(record_id='policy-004',event_id=None,title='Contact verification',rule='An active directory match, explicit registration evidence and a matching invitation are required for verified export. Missing, duplicate or conflicting records require review.',authority='Event Operations')]
people=[]
for i,name,email,org,active,ids in [(1,'Amara Dlamini','amara@example.org','Cedar Collective',True,[101,102]),(2,'Ben Jacobs','ben@example.org','Northline Labs',True,[101,103]),(3,'Cara Naidoo','cara@example.org','Cedar Collective',True,[101,102]),(4,'Daniel Mokoena','daniel@example.org','Harbour Network',False,[101]),(5,'Elena Petersen','elena@example.org','Harbour Network',True,[101,103]),(6,'Farai Ncube','farai@example.org','Northline Labs',True,[102,103])]:
    people.append(dict(record_id=f'directory-{i:03}',participant_id=f'P-{i:03}',name=name,email=email,organization=org,active=active,event_ids=[f'EVT-{n}' for n in ids]))
save(Path('data/structured/events.json'),events);save(Path('data/structured/policies.json'),policies);save(Path('data/structured/directory.json'),people)
calendar={};emails={}
for ev in events:
    eid=ev['event_id']; selected=[p for p in people if eid in p['event_ids']]
    calendar[eid]=[dict(id='cal-'+eid,summary=eid+' '+ev['name'],start={'dateTime':ev['date']+'T09:00:00+02:00'},end={'dateTime':ev['date']+'T16:00:00+02:00'},attendees=[dict(displayName=p['name'],email=p['email'],responseStatus='accepted') for p in selected])]
    emails[eid]=[dict(id=f'mail-{eid}-{p["participant_id"]}',subject=f'Registration {eid}',body=f'I am registering for {eid}. Name: {p["name"]}. Email: {p["email"]}. Participant: {p["participant_id"]}. Organization: {p["organization"]}.',fixture_attendee=dict(name=p['name'],email=p['email'],participant_id=p['participant_id'],organization=p['organization'],event_id=eid,source_id=f'mail-{eid}-{p["participant_id"]}',source_type='gmail')) for p in selected]
# Controlled discrepancies, preserving original content and structured fixture truth.
for m in emails['EVT-101']:
    if m['fixture_attendee']['participant_id']=='P-003':
        m['body']=m['body'].replace('Cara Naidoo','Carla Naidoo');m['fixture_attendee']['name']='Carla Naidoo'
    if m['fixture_attendee']['participant_id']=='P-005':
        m['body']=m['body'].replace('Harbour Network','Harbour Consulting');m['fixture_attendee']['organization']='Harbour Consulting'
duplicate=json.loads(json.dumps(emails['EVT-101'][1])); duplicate['id']='mail-EVT-101-duplicate';duplicate['fixture_attendee']['source_id']=duplicate['id'];emails['EVT-101'].append(duplicate)
for sid,name,email,pid in [('missing-email','Gina Smith',None,None),('unknown','Hugo Botha','hugo@example.org','P-099')]:
    emails['EVT-101'].append(dict(id='mail-'+sid,subject='Registration EVT-101',body=f'Register EVT-101: {name}. Email: {email or "not supplied"}',fixture_attendee=dict(name=name,email=email,participant_id=pid,organization=None,event_id='EVT-101',source_id='mail-'+sid,source_type='gmail')))
save(Path('data/fixtures/calendar.json'),calendar);save(Path('data/fixtures/emails.json'),emails)
save(Path('data/fixtures/expected.json'),{'EVT-101':{'verified':['amara@example.org'],'review_required':['ben@example.org','cara@example.org','daniel@example.org','elena@example.org','Gina Smith'],'unverified':['hugo@example.org']},'EVT-102':{'verified':['amara@example.org','cara@example.org','farai@example.org']},'EVT-103':{'verified':['ben@example.org','elena@example.org','farai@example.org']}})
save(Path('data/structured/organizations.json'),[{'organization_id':'ORG-001','name':'Cedar Collective'},{'organization_id':'ORG-002','name':'Northline Labs'},{'organization_id':'ORG-003','name':'Harbour Network'}])
