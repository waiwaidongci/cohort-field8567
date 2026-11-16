import {request,post} from './client';import type {Run} from '../types/domain';
export const getRuns=()=>request<Run[]>('/runs');
export const getRun=(id:number)=>request<Run>('/runs/'+id);
export const createRun=(data:unknown)=>post<Run>('/runs',data);
