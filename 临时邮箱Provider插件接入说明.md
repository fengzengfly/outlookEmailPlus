# 临时邮箱 Provider 插件接入说明

> 适用对象：准备为 OutlookMail Plus 接入一个新的临时邮箱 Provider 的开发者。
>
> 这不是“插件系统怎么实现”的设计文档，而是一份**面向接入者**的落地说明：告诉你一个 Provider 插件需要长什么样、放在哪里、如何配置、如何验收。

---

## 1. 你要接入的到底是什么

当前项目已经完成临时邮箱 Provider 插件化。对接一个新的 Provider，不需要再改 Route / Controller / Service 主干，也不需要改现有 `/api/temp-emails/*` 或 `/api/external/temp-emails/*` 路径。

你真正要做的，通常只有两件事：

1. 写一个符合 `TempMailProviderBase` 契约的 Provider 类
2. 让系统能发现它（本地文件放置或通过 registry 安装）

接入完成后，这个插件会和内置 Provider 一样：

- 出现在设置页「插件管理」
- 出现在临时邮箱 Provider 选项里
- 走现有 temp-mail 用户侧与 external 侧链路
- 支持热刷新，不需要重启容器

---

## 2. 当前真实路径口径

这点非常重要：**运行时插件目录不是固定仓库根 `plugins/`**。

当前代码实际使用的是：

- registry 文件：`<DATABASE_PATH 上级目录>/plugins/registry.json`
- 插件目录：`<DATABASE_PATH 上级目录>/plugins/temp_mail_providers/`

也就是说：

1. **开发仓库里提交的插件样例/官方插件源**可以放在仓库根 `plugins/`
2. **程序运行时真正扫描和安装的目录**是 `<DATABASE_PATH 上级目录>/plugins/...`

如果你是在部署环境里手工投放插件文件，请以运行时路径为准。

---

## 3. 一个 Provider 插件最小需要实现什么

Provider 必须继承：

- `outlook_web.services.temp_mail_provider_base.TempMailProviderBase`

并通过装饰器注册：

- `@register_provider`

最小骨架如下：

```python
from __future__ import annotations

from typing import Any

from outlook_web.services.temp_mail_provider_base import TempMailProviderBase, register_provider


@register_provider
class DemoTempMailProvider(TempMailProviderBase):
    provider_name = "demo_temp_mail"
    provider_label = "Demo Temp Mail"
    provider_version = "0.1.0"
    provider_author = "Your Team"
    config_schema = {
        "fields": [
            {"key": "base_url", "label": "Base URL", "type": "url", "required": True},
            {"key": "api_key", "label": "API Key", "type": "password", "required": True},
        ]
    }

    def get_options(self) -> dict[str, Any]:
        return {
            "domain_strategy": "auto_or_manual",
            "default_mode": "auto",
            "domains": [{"name": "demo.example", "enabled": True, "is_default": True}],
            "prefix_rules": {"min_length": 1, "max_length": 32, "pattern": "^[a-z0-9][a-z0-9._-]*$"},
            "provider": self.provider_name,
            "provider_name": self.provider_name,
            "provider_label": self.provider_label,
        }

    def create_mailbox(self, *, prefix: str | None = None, domain: str | None = None) -> dict[str, Any]:
        return {"success": True, "email": "demo@demo.example", "meta": {}}

    def delete_mailbox(self, mailbox: dict[str, Any]) -> bool:
        return True

    def list_messages(self, mailbox: dict[str, Any]) -> list[dict[str, Any]] | None:
        return []

    def get_message_detail(self, mailbox: dict[str, Any], message_id: str) -> dict[str, Any] | None:
        return None

    def delete_message(self, mailbox: dict[str, Any], message_id: str) -> bool:
        return True

    def clear_messages(self, mailbox: dict[str, Any]) -> bool:
        return True
```

---

## 4. 类属性怎么设计

### 4.1 必填元信息

| 字段 | 说明 |
|------|------|
| `provider_name` | 唯一标识，建议小写 snake_case |
| `provider_label` | 显示给用户看的名称 |
| `provider_version` | 插件版本 |
| `provider_author` | 作者/团队 |

### 4.2 `config_schema`

设置页插件管理会根据 `config_schema.fields` 自动渲染配置表单。

当前前端已支持的字段类型：

- `text`
- `password`
- `textarea`
- `number`
- `select`
- `url`
- `toggle`

建议每个字段至少包含：

```python
{
    "key": "base_url",
    "label": "Base URL",
    "type": "url",
    "required": True,
    "placeholder": "https://api.example.com",
    "default": ""
}
```

插件配置最终会存进 `settings` 表，key 形式为：

```text
plugin.{provider_name}.{field_key}
```

---

## 5. 各方法的返回口径

## 5.1 `get_options()`

建议返回：

```python
{
    "domain_strategy": "auto_or_manual",
    "default_mode": "auto",
    "domains": [
        {"name": "a.example", "enabled": True, "is_default": True},
        {"name": "b.example", "enabled": True, "is_default": False},
    ],
    "prefix_rules": {
        "min_length": 1,
        "max_length": 32,
        "pattern": "^[a-z0-9][a-z0-9._-]*$",
    },
    "provider": self.provider_name,
    "provider_name": self.provider_name,
    "provider_label": self.provider_label,
}
```

这个方法除了给前端渲染域名/前缀规则，也会被“测试连接”用来验证 Provider 是否可连通。

## 5.2 `create_mailbox()`

建议成功返回：

```python
{"success": True, "email": "user@example.com", "meta": {...}}
```

建议失败返回：

```python
{"success": False, "error": "上游错误说明", "error_code": "UPSTREAM_SERVER_ERROR"}
```

`meta` 建议放入后续读信/删信所需的 provider 侧标识，例如：

- provider mailbox id
- token / jwt
- domain id
- account id

## 5.3 `list_messages()`

建议返回平台标准结构列表。每一项至少建议包含：

```python
{
    "id": "provider_unique_message_id",
    "message_id": "provider_unique_message_id",
    "from_address": "sender@example.com",
    "subject": "hello",
    "content": "text body",
    "html_content": "<p>html body</p>",
    "has_html": True,
    "timestamp": 1710000000,
}
```

`id` / `message_id` 应稳定且唯一，避免不同 Provider 之间冲突。

## 5.4 `get_message_detail()`

返回单封邮件的完整结构；如果上游没有单独的 detail 接口，可以像 CF Provider 那样通过 `list_messages()` 回退过滤。

## 5.5 `delete_message()` / `clear_messages()` / `delete_mailbox()`

这三个方法建议直接返回 `bool`。如果上游失败，优先显式返回 `False`，不要伪装成功。

---

## 6. 插件如何被系统发现

## 6.1 本地直接投放

把插件文件放到：

```text
<DATABASE_PATH 上级目录>/plugins/temp_mail_providers/{provider_name}.py
```

然后在页面点击：

- 设置 → 临时邮箱 → 插件管理 → 应用变更

或者调用：

```bash
POST /api/system/reload-plugins
```

## 6.2 通过插件源安装

如果你希望它出现在“可安装”列表中，还需要在 registry 里提供条目：

```json
{
  "name": "demo_temp_mail",
  "display_name": "Demo Temp Mail",
  "version": "0.1.0",
  "author": "Your Team",
  "description": "一个示例插件",
  "download_url": "https://example.com/demo_temp_mail.py",
  "sha256": "文件SHA256",
  "min_app_version": "1.13.0",
  "dependencies": ["requests>=2.32.0"]
}
```

---

## 7. 当前真实 UI / API 行为

这部分是本次会话已经验证过的真实结论：

1. `POST /api/system/reload-plugins` 返回 `failed` 列表
2. `GET /api/plugins` 现在会聚合：
   - available
   - installed
   - failed
3. 加载失败的插件会在 UI 中显示为：
   - `status = load_failed`
   - 并带回 `error`
4. 页面点击“应用变更”后，故障插件会真实显示“加载失败”卡片，而不是伪装成 installed

也就是说，接入新 Provider 时，如果导入失败，管理员现在能直接在 UI 中看到错误原因。

---

## 8. 推荐接入步骤

1. 先整理目标 Provider 的 API 文档
   - 域名列表接口
   - 创建邮箱接口
   - 邮件列表接口
   - 单封详情接口（如有）
   - 删除单封 / 清空邮箱 / 删除邮箱接口
   - 鉴权方式
2. 写 Provider 类
3. 本地放到运行时插件目录
4. 点击“应用变更”确认已成功加载
5. 在插件管理里完成配置保存与测试连接
6. 到临时邮箱页面实际创建邮箱并读信
7. 再走 external temp-mail 链路做一次任务侧验收

---

## 9. 最小验收清单

至少确认以下 8 项：

1. 插件能被加载，且在插件管理中显示
2. 配置表单能正确渲染
3. “测试连接”通过
4. 能成功创建邮箱
5. 能读取消息列表
6. 能读取单封详情
7. 能删除单封 / 清空邮箱 / 删除邮箱
8. 加载失败时 UI 会真实显示错误卡片

---

## 10. 相关文档

- `docs/FD/2026-04-21-临时邮箱插件化FD.md`
- `docs/TD/2026-04-21-临时邮箱插件化TD.md`
- `docs/TDD/2026-04-21-临时邮箱插件化TDD.md`
- `docs/TODO/2026-04-21-临时邮箱插件化TODO.md`
- `临时邮箱Provider插件接入提示词.md`
