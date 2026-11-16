-- Schema v2: segment_runs.constraints 保存实验页录入的同群 / 异群约定与每群人数范围。
-- 既有实验该列为 NULL（视为无约束），历史实验与获批名单保持原结果不变。
-- 后端启动时由 src/config/database.py 的 ensure_schema_upgrades 幂等应用。
ALTER TABLE segment_runs ADD COLUMN constraints JSON NULL;
