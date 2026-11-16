export interface User {id:number;name:string;email:string;role:string}
export interface Dataset {id:number;name:string;source_file:string;description:string;row_count:number}
export interface Customer {id:number;code:string;recency:number;frequency:number;spend:number;learning_days:number}
export interface Candidate {k:number;silhouette?:number;inertia?:number;feasible?:boolean;note?:string}
export interface RunConstraints {must_link?:string[][];cannot_link?:string[][];size_min?:number|null;size_max?:number|null}
export interface ConstraintCheck {type:string;codes:string[];satisfied:boolean;detail:string}
export interface SizeCheck {label:number;size:number;min:number;max:number;satisfied:boolean}
export interface Run {id:number;name:string;dataset_id:number;features:string[];k_min:number;k_max:number;status:string;error:string;created_at:string;constraints?:RunConstraints|null;result:{best_k?:number;silhouette?:number;sample_count?:number;checksum?:string;seed?:number;candidates?:Candidate[];constraint_checks?:ConstraintCheck[];size_checks?:SizeCheck[];sample?:{code:string;recency:number;spend:number;label:number}[]}}
export interface Segment {id:number;run_id:number;label:number;name:string;size:number;center:Record<string,number>;recommendation:string}
export interface Campaign {id:number;name:string;segment_id:number;segment_name:string;size:number;note:string;status:string;created_at:string}
export interface Audit {id:number;actor:string;action:string;status_code:number;created_at:string}
export function hasConstraints(run:Run):boolean {const c=run.constraints;return !!(c&&((c.must_link?.length)||(c.cannot_link?.length)||c.size_min!=null||c.size_max!=null));}
