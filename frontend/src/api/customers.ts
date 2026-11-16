import {request} from './client';import type {Customer} from '../types/domain';
export const getCustomers=(dataset:number,search='',offset=0)=>request<{total:number;rows:Customer[]}>(`/customers?dataset_id=${dataset}&search=${encodeURIComponent(search)}&offset=${offset}&limit=20`);
