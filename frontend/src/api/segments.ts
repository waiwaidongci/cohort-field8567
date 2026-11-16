import {request} from './client';import type {Segment} from '../types/domain';
export const getSegments=(run?:number)=>request<Segment[]>('/segments'+(run?'?run_id='+run:''));
