export interface User {id:number;name:string;email:string;role:string}
export interface Dataset {id:number;name:string;source_file:string;description:string;row_count:number}
export interface Customer {id:number;code:string;recency:number;frequency:number;spend:number;learning_days:number}
export interface Candidate {k:number;silhouette:number;inertia:number}
export interface Run {id:number;name:string;dataset_id:number;features:string[];k_min:number;k_max:number;status:string;error:string;created_at:string;result:{best_k?:number;silhouette?:number;sample_count?:number;checksum?:string;seed?:number;candidates?:Candidate[];sample?:{code:string;recency:number;spend:number;label:number}[]}}
export interface Segment {id:number;run_id:number;label:number;name:string;size:number;center:Record<string,number>;recommendation:string}
export interface Campaign {id:number;name:string;segment_id:number;segment_name:string;size:number;note:string;status:string;created_at:string}
export interface Audit {id:number;actor:string;action:string;status_code:number;created_at:string}
