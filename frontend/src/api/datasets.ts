import {request,post} from './client';import type {Dataset} from '../types/domain';
export const getDatasets=()=>request<Dataset[]>('/datasets');
export const importDataset=(data:unknown)=>post<{id:number;row_count:number}>('/datasets',data);
