# Changelog

All notable changes to OutlookMail Plus are documented in this file.

## [v1.11.0] - 2026-04-03

### 新功能 / New Features

- **邮箱池项目隔离（PR#27）**：在 `claim-random` 时支持传入 `project_key`，同一 `caller_id + project_key` 下已使用的账号不会被重复领取（DB 迁移 v17）
- **CF Worker 临时邮箱多域支持**：可在设置页配置多个 CF Worker 域名；新增"同步域名"按钮，支持前端一键刷新域名列表
- **CF Worker Admin Key 加密存储**：`cf_worker_admin_key` 现在以 `enc:` 前缀加密写入数据库，不再以明文存储（DB 迁移 v18）

### 修复 / Bug Fixes

- **BUG-06**：生成或删除临时邮箱后，列表中已选中的邮箱状态得到正确保留，不再因刷新而丢失选中高亮
- **BUG-07**：临时邮箱面板在刷新邮件列表后，域名下拉选择不再被意外重置回默认值

### i18n

- 临时邮箱面板域名提示文字（`domain_hint_xxx`）新增中英双语翻译
- CF Worker 域名同步按钮 (`sync_cf_domains`)、提示文字 (`cf_domain_hint`) 新增双语支持

### CI / 代码质量修复

- 修复 `pool.py` 中存在的重复函数定义（`release`、`complete`、`expire_stale_claims`、`recover_cooldown`、`get_stats`）
- 修复 `pool.py` `get_stats()` 后的死代码（`return` 之后的不可达 `claim` 函数体）
- 修复 `RESULT_TO_POOL_STATUS` 中 `"success"` 映射：由旧的 `"cooldown"` 改为正确的 `"used"`
- 修复 `get_stats()` 的 `pool_counts` 字典，补充缺失的 `"used": 0` 键
- 修复 `pool.py` `claim_atomic()` 中 black 格式化问题（`cutoff`、`lease_expires_at_str` 多行表达式）
- 在 `external_api.py` 中添加 `# noqa: E203`、`# noqa: C901` 压制 flake8 误报
- 对齐 `test_pool.py` 和 `test_pool_flow_suite.py` 中的测试断言，统一期望 `success` 完成后状态为 `"used"`
- 全量 `black --line-length 127` 与 `isort --profile black` 格式化

---

## [v1.10.0] - 2026-03-26

- OAuth 回归修复与认证后工作区重构

## [v1.9.2] - 2026-03-24

- 小版本修复

## [v1.9.0] - 2026-03-20

- 双语界面、统一通知分发与演示站点保护

## [v1.7.0] - 2026-03-15

- 第二次发布：README 交付口径补全

## [v1.6.1] - 2026-03-15

- 发布质量闸门清理与发布内容精简
