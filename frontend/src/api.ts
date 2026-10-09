export const API = (import.meta as unknown as {env: Record<string,string>}).env.VITE_API_URL || 'http://localhost:5050';
export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
  const response = await fetch(API+'/api'+path, { ...options, credentials:'include', headers:{'Content-Type':'application/json',...options.headers} });
  if (!response.ok) {
    const body = await response.json().catch(()=>({detail:'Service unavailable. Check the backend connection.'}));
    throw new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail));
  }
  return response.json();
}
export type Evidence={id?:string;source_type?:string;source_id?:string;text?:string;score?:number;source?:{file:string;record_id:string};original?:unknown};
export type Message={id:string;role:string;content:string;evidence:Evidence[];details?:{mode?:string;supported?:boolean;query?:string}};
export type Run={id:string;objective:string;event_id:string;mode:string;status:string;created_at:string;error:string|null;state:{plan?:{tools:string[];rationale:string}};events?:{id:string;created_at:string;stage:string;outcome:string;detail:unknown}[]};
export type Result={id:string;status:string;record:{name:string|null;email:string|null;organization:string|null;participant_id:string|null};reasons:string[];evidence:Evidence[]};
export type Status={mode:string;gemini_configured:boolean;google_connected:boolean;oauth_configured:boolean;directory_configured:boolean;transport:string;worker_enabled:boolean};
