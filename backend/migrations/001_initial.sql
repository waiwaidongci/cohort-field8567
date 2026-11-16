-- Schema v1 is materialized from SQLAlchemy metadata at boot for this isolated demo.
-- Natural keys: users.email, datasets.name, (customers.dataset_id,code),
-- segment_runs.name, (segments.run_id,label), campaigns.name.
-- For future schema changes introduce a versioned migration before changing metadata.
SELECT 'cohort-field schema v1';
