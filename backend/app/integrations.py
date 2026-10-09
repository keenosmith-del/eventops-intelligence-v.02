import base64
import json
import time
from urllib.parse import urlparse
import httpx
from cryptography.fernet import Fernet
from .config import settings, ROOT
from .db import DB, Credential, log_event
from .schemas import Participant

class ToolFailure(RuntimeError): pass

def cipher():
    if not settings().token_encryption_key: raise ToolFailure('TOKEN_ENCRYPTION_KEY is not configured')
    return Fernet(settings().token_encryption_key.encode())
def store_token(payload):
    with DB() as db:
        previous=db.get(Credential,'google')
        old=json.loads(cipher().decrypt(previous.encrypted.encode())) if previous else {}
        old.update(payload);old['expires_at']=time.time()+payload.get('expires_in',3600)-60
        db.merge(Credential(id='google',encrypted=cipher().encrypt(json.dumps(old).encode()).decode()));db.commit()
def request_json(method,url,run_id=None,stage=None,**kwargs):
    for attempt in range(3):
        try:
            with httpx.Client(timeout=httpx.Timeout(20,connect=5), follow_redirects=False) as client:
                response=client.request(method,url,**kwargs)
                response.raise_for_status()
                if len(response.content)>2_000_000: raise ToolFailure('External response exceeded size limit')
                return response.json()
        except (httpx.TimeoutException,httpx.NetworkError,httpx.HTTPStatusError) as exc:
            transient=not isinstance(exc,httpx.HTTPStatusError) or exc.response.status_code in (429,500,502,503,504)
            if attempt==2 or not transient: raise ToolFailure('External request failed'+(f' (HTTP {exc.response.status_code})' if isinstance(exc,httpx.HTTPStatusError) else ' (network or timeout)')) from exc
            if run_id: log_event(run_id,stage or 'http','retry',{'attempt':attempt+1,'backoff_seconds':0.5*2**attempt})
            time.sleep(0.5*2**attempt)
        except (ValueError,TypeError) as exc: raise ToolFailure('External response is malformed JSON') from exc
    raise ToolFailure('Request exhausted')
def google_token():
    with DB() as db:
        saved=db.get(Credential,'google')
        if not saved: raise ToolFailure('Google account is not connected')
        token=json.loads(cipher().decrypt(saved.encrypted.encode()))
    if token['expires_at']<=time.time():
        if not token.get('refresh_token'): raise ToolFailure('Google authorization expired; reconnect the test account')
        cfg=settings()
        token.update(request_json('POST','https://oauth2.googleapis.com/token',data={'client_id':cfg.google_client_id,'client_secret':cfg.google_client_secret,'refresh_token':token['refresh_token'],'grant_type':'refresh_token'}));store_token(token)
    return token['access_token']

def decode_body(payload):
    parts=payload.get('parts',[])
    if parts: return '\n'.join(decode_body(p) for p in parts if p.get('mimeType')!='text/html')[:20000]
    if payload.get('mimeType') not in ('text/plain',None): return ''
    data=payload.get('body',{}).get('data','')
    return base64.urlsafe_b64decode(data+'='*(-len(data)%4)).decode('utf-8',errors='replace')[:20000]

class Tools:
    def __init__(self,run_id): self.run_id=run_id;self.cfg=settings()
    def call(self,tool,event_id):
        if self.cfg.mode=='fixture':
            if tool=='web': return json.loads((ROOT/'data/structured/directory.json').read_text())
            return json.loads((ROOT/f'data/fixtures/{"calendar" if tool=="calendar" else "emails"}.json').read_text()).get(event_id,[])
        if self.cfg.integration_transport=='n8n':
            if not self.cfg.n8n_webhook_secret: raise ToolFailure('N8N_WEBHOOK_SECRET is not configured')
            response=request_json('POST',self.cfg.n8n_base_url.rstrip('/')+'/webhook/eventops-'+tool,self.run_id,tool,headers={'X-EventOps-Key':self.cfg.n8n_webhook_secret},json={'event_id':event_id})
            if not isinstance(response,dict) or not isinstance(response.get('data'),list) or response.get('complete') is not True: raise ToolFailure('Invalid or truncated n8n response envelope')
            result=response['data']
        elif tool=='web':
            url=self.cfg.directory_url; parsed=urlparse(url)
            if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password: raise ToolFailure('DIRECTORY_URL must be an operator-configured HTTPS endpoint')
            result=request_json('GET',url,self.run_id,tool)
        else:
            headers={'Authorization':'Bearer '+google_token()}
            if tool=='calendar':
                from urllib.parse import quote
                url='https://www.googleapis.com/calendar/v3/calendars/'+quote(self.cfg.calendar_id,safe='')+'/events'
                response=request_json('GET',url,self.run_id,tool,headers=headers,params={'q':event_id,'maxResults':100,'singleEvents':'true'})
                if response.get('nextPageToken'): raise ToolFailure('Calendar results exceed bounded limit; narrow the dedicated test calendar')
                result=[e for e in response.get('items',[]) if event_id in e.get('summary','') or event_id in e.get('description','')]
            elif tool=='gmail':
                base='https://gmail.googleapis.com/gmail/v1/users/me/messages'
                response=request_json('GET',base,self.run_id,tool,headers=headers,params={'q':f'subject:({event_id})','maxResults':30})
                if response.get('nextPageToken'): raise ToolFailure('Gmail results exceed bounded limit; narrow the dedicated test mailbox')
                result=[]
                for m in response.get('messages',[]):
                    message=request_json('GET',base+'/'+m['id'],self.run_id,tool,headers=headers,params={'format':'full'})
                    payload=message.get('payload',{});subject=next((h['value'] for h in payload.get('headers',[]) if h['name'].lower()=='subject'),'')
                    result.append({'id':m['id'],'subject':subject,'body':decode_body(payload)})
            else: raise ToolFailure('Tool is not allowed')
        if not isinstance(result,list) or len(result)>500: raise ToolFailure('Invalid external records')
        if tool=='web':
            try: result=[Participant.model_validate(r).model_dump() for r in result]
            except ValueError as exc: raise ToolFailure('Invalid directory schema') from exc
        return result
