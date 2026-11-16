import {request,post} from './client';import type {Campaign} from '../types/domain';
export const getCampaigns=()=>request<Campaign[]>('/campaigns');
export const createCampaign=(data:unknown)=>post<Campaign>('/campaigns',data);
export const approveCampaign=(id:number)=>request<Campaign>('/campaigns/'+id+'/approve',{method:'PATCH'});
export async function exportCampaign(id:number){const r=await fetch(`/api/campaigns/${id}/export`,{headers:{Authorization:'Bearer '+localStorage.getItem('cohort-token')}});if(!r.ok){const e=await r.json();throw new Error(e.detail);}const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download=`weian-campaign-${id}.csv`;a.click();URL.revokeObjectURL(url);}
