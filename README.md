# 苇岸客户留存分群 · Cohort Field

把匿名消费与学习特征变成可复算的人群研究，再交付经过批准的触达名单。

苇岸学习社的 18 名运营分析人员原来每周在表格按消费档分组，手工圈选客户。高消费但沉默的人群容易被漏掉，消费金额压过活跃特征，K 值也缺少比较依据。本项目接收上游匿名特征，替代分群研究、解释、方案审批与名单交付这一段，下游运营团队使用 CSV；不会向客户发送消息。

## 启动

```sh
cp .env.example .env
docker compose up -d --build
docker compose ps
# 可选：重复执行不会覆盖用户修改或追加重复记录
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18201，后端 http://localhost:19201，API 文档 http://localhost:19201/docs。Nginx 的 `/api/` 去掉前缀转发，直接访问后端时无 `/api`。

完成后：`docker compose down -v --remove-orphans`，会删除本项目演示数据。

## 账号与角色

共用密码：`Weian2026!`。

| 邮箱 | 角色 | 页面与权限 | 典型动作 |
|---|---|---|---|
| admin@weian.demo | admin / 运营负责人 | 全部六页；可新建、审批、下载 | 批准“冬季复学关怀”名单 |
| analyst@weian.demo | analyst / 研究员 | 全部六页；可导入、计算、拟定方案；不能批准 | 比较 K 后创建复学方案 |
| viewer@weian.demo | viewer / 内容阅读者 | 全部六页只读；可下载已批准名单 | 阅读群组解释并取走匿名 CSV |

读取审计在三个团队角色中开放，拒绝的写操作也记录状态码。密码使用带盐 PBKDF2-SHA256；JWT 有效期 8 小时。后端每分钟限制同来源 30 次登录请求。全局错误恢复提示与审计分别为独立中间件。演示凭证仅供本地运行；对外部署前修改环境变量与演示账户。

## 一天的工作剧本

1. 09:00 陈岸用 analyst 账号进入研究首页，检查 720 位匿名学习者。
2. 09:05 到客户数据打开 `wei-an-members-202611.csv` 的 90 天汇总，检索 `WA-0021`。
3. 09:10 建立“冬季复学 · 四维分群”，选 recency、frequency、spend、learning_days。
4. 09:12 设候选 K 为 2–6，提交队列；worker 执行 Python 计算。
5. 09:13 查看轮廓系数比较，阅读“沉默高价值”人群的原量纲中心。
6. 09:20 以该群组拟定“冬季复学 · 进度回顾”，填写 14 天复盘计划。
7. 09:30 沈苇使用 admin 账号批准；研究员不能自行批准。
8. 09:35 林禾用 viewer 账号下载匿名名单 CSV；在研究留痕核对审批与导出证据。

## 真实计算

- 输入：10–5000 行匿名客户；唯一 `code`，四个有限非负特征。CSV 表头为 `code,recency,frequency,spend,learning_days`。导入通过文本框提交，不保留上传原文件。
- 算法一：对所选至少两个特征做 Z-score：`z=(x−mean)/std`；KMeans（`random_state=42,n_init=10`）计算候选 K。原量纲群组中心用于解释。
- 算法二：计算每个候选的轮廓系数 `s=(b−a)/max(a,b)`，取均值最高者，同分选较小 K；保存所有候选的 inertia 与系数。
- 业务解释：中心 recency≥55 且 spend≥700 为“沉默高价值”；recency≤25 且 frequency≥8 为“活跃深度学习”；spend<400 为“轻量探索”；其余为“稳定潜力”。标签只是明确规则产生的观察线索，不是因果结论。
- 失败态：常量列、非有限值、重复特征、未知特征、样本不足、不同观测行不足和非法 K 范围；异步失败保存状态与原因，页面会显示恢复提示。
- 可复算：固定种子 42，按客户主键排序，保存数值矩阵 SHA256、特征列表、候选范围。seed 创建 720 位客户、3 次独立研究、2 个方案，不覆盖已存在自然键记录。客户数据集不可修改，旧研究与名单对应固定数据。
- 散点来自真实聚类标记，按群组分层随机展示最多 180 个样本（seed=42，每群均分配额，确保覆盖所有群组）；坐标为 recency 与 spend，超出显示范围的点在图边界截断，完整数据可在客户表与批准 CSV 查看。

## 技术与目录

| 层 | 实现 |
|---|---|
| frontend | Vue 3 / TypeScript / Pinia / Vue Router / Vite，Nginx SPA |
| backend | Python 3.11 / FastAPI / SQLAlchemy / PyMySQL / PyJWT |
| worker | Python 持久化队列消费者，Redis 唤醒、MySQL 任务状态为事实源 |
| db | MySQL 8.0 |
| redis | Redis 7，AOF 命名卷与登录限流 |
| 算法 | NumPy / scikit-learn KMeans、StandardScaler、silhouette_score |

`frontend/src/{api,stores,types,components/common,hooks,pages,router,utils,constants}`。`backend/src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}`。`backend/scripts/seed_demo.py`。`backend/migrations/001_initial.sql` 说明 v1 自然键与初始 schema，启动由 metadata 创建；后续真实升级应添加版本迁移。

五个核心实体 Dataset、Customer、SegmentRun、Segment、Campaign 各有 model/schema/service/controller/route/API，并经 Pinia store 进入页面。Overview 与 Segments 共用 SegmentSummary，Overview 与 Experiments 共用 RunTable，页面共用 PageHeading、StatusBadge、ErrorNotice、EmptyState。useTask 管理恢复状态，usePolling 管理运行中刷新。

## 环境变量与 Docker

| 变量 | 默认用途 |
|---|---|
| COMPOSE_PROJECT_NAME | cohort-field；控制所有容器命名，支持中文父目录 |
| FRONTEND_PORT / BACKEND_PORT / DB_PORT | 18201 / 19201 / 17701 |
| DB_PASSWORD | 本地 MySQL 密码 |
| JWT_SECRET | JWT 签名，部署前替换 |
| SEED_DEMO | true 启动自动 seed；失败记录日志并允许服务启动 |

恰好五服务，各有健康检查。backend 等 db/redis healthy；worker 另等 backend 完成初始化；frontend 等 backend healthy。数据库、Redis、共享分析产物分别有命名卷；当前任务结果与名单在 DB 实时生成，共享产物卷保留为未来大文件导出通道。worker 用心跳文件检查；启动或重启时扫描 queued/running 状态并恢复。单 worker 部署，不声称支持多个并发 worker 抢占同一任务。

本地开发：启动 db/redis 后，后端安装 `requirements.txt`，设置 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，执行 `uvicorn src.main:app --reload`（在 backend 目录）；另开终端执行 `python -m src.worker`。前端 `npm install && npm run dev`，Vite 将 `/api/` 转发到 19201。测试脚本与截图在批次根的 `test-artifacts/gb-0002/`，不在源码中。

## 共享枚举位置

| 枚举 | 后端 | 前端及使用处 |
|---|---|---|
| Role | `backend/src/constants/enums.py`；授权 `utils/auth.py`，seed角色值一致 | `frontend/src/constants/enums.ts`；auth store、App 角色展示、Campaigns 审批 |
| RunStatus | `backend/src/constants/enums.py`；run_service/worker 使用一致状态值 | `frontend/src/constants/enums.ts`；StatusBadge、Experiments、Segments |
| CampaignStatus | `backend/src/constants/enums.py`；campaign_service | `frontend/src/constants/enums.ts`；Campaigns、StatusBadge |
| FEATURES | `backend/src/constants/enums.py`；schema 校验、计算、名单导出 | `frontend/src/constants/enums.ts`；Experiments 特征配置 |

License：MIT，见 LICENSE。
