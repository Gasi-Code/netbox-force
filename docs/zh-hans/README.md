# NetBox Force — 指南（简体中文）

[← 所有语言](../README.md) · [项目 README](../../README.md) · [变更记录](../../CHANGELOG.md)

---

## 1. 插件的作用

NetBox 记录*改了什么*。NetBox Force 则决定*这项改动是否被允许*，并可以在放行之前
要求给出理由。

它位于每一次保存与删除操作和数据库之间。在改动被写入之前，它可以检查：

- 是否填写了变更说明，长度是否足够
- 说明是否只由无实质内容的词构成
- 说明中是否引用了工单编号
- 改动是否发生在获准的时间窗口内
- 字段取值是否符合命名规则
- 必填字段是否确实已填写

随之还有两个模块：

- **补丁管理** — 每台虚拟机或物理服务器的补丁状态、操作系统、责任人和更新历史，
  可选择由 CheckMK 供给数据。
- **Graylog** — 把审计事件送出去，并把日志信息带回到它所属的对象旁边。

一切都是可选的。安装后仅启用变更说明的存在性检查，最少两个字符。其余功能在 Web
界面中开启。

---

## 2. 前提条件

| 组件 | 版本 | 说明 |
|---|---|---|
| NetBox | 4.0.0 或更高 | |
| Python | 3.10 或更高 | |
| PostgreSQL | — | NetBox 本身要求 |
| `cryptography` | 任意 | 随 NetBox 提供。缺少时 CheckMK 密钥和 Graylog 令牌将以明文保存，插件会在设置页面说明这一点 |
| `requests` | 任意 | 随 NetBox 提供。CheckMK 和 Graylog 需要 |
| RQ 进程 | — | 仅用于计划的 CheckMK 同步和 Graylog 轮询。没有它两者仍可按需运行，页面会说明这一点 |

---

## 3. 安装

### 3.1 安装软件包

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 注册插件

在 `configuration.py` 中：

```python
PLUGINS = ['netbox_force']
```

### 3.3 执行迁移

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 重启 NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <容器> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <容器> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <容器>
```

在 LinuxServer.io 镜像上**不要**使用 `custom-cont-init.d` 脚本来安装。它们在 NetBox
自身的初始化脚本*之后*运行，可能导致迁移失败。Docker Mods 在其之前运行。

在容器文件系统内完成的安装无法在镜像更新后保留。请把插件加入镜像的持久化插件安装
机制，否则下次 pull 之后它就不见了。

---

## 4. 更新

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

需要 `--force-reinstall --no-cache-dir`，因为 pip 按版本号缓存，否则会跳过同一版本的
重新构建。

**重启之前先检查。** 这一步在不触碰运行中进程的情况下加载插件。若报错，请不要重启：
运行中的 NetBox 内存里仍是旧代码，会继续工作。

```bash
cd /opt/netbox/netbox
python manage.py check
```

然后：

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### 回退到旧版本

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

通常无需为此回滚迁移。多出的列不会干扰旧代码——它只是不认识这些列。即便如此，更新前
仍请备份数据库。

---

## 5. 配置文件

`PLUGINS_CONFIG` **只设定初始值**。首次启动之后，每一项设置都在 Web 界面中管理并保存
在数据库中。

```python
PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
        'checkmk_secret': '',
    },
}
```

| 设置 | 默认值 | 含义 |
|---|---|---|
| `min_length` | `2` | 变更说明的最少字符数 |
| `exempt_users` | 见上 | 豁免所有检查的用户名，不区分大小写 |
| `enforce_on_create` | `False` | 创建时也要求填写说明 |
| `enforce_on_delete` | `True` | 删除时也要求填写说明 |
| `extra_exempt_models` | `[]` | 额外豁免的模型，格式 `app.model` |
| `checkmk_secret` | `''` | 可选。让 CheckMK 密钥完全不进入数据库；设置后其优先级高于界面中的输入框 |

---

## 6. 各页面

超级用户可在侧边栏找到 **NetBox Force**。除另有说明外，所有页面仅限超级用户访问。

| 页面 | 用途 |
|---|---|
| **设置** | 全部强制规则、豁免、模块、Webhook、CheckMK |
| **校验规则** | 命名规则与必填字段，按模型和字段设置 |
| **模型策略** | 按模型对全局设置的例外 |
| **违规** | 每一次被拦截改动的可筛选记录，可导出为 CSV |
| **Graylog** | 发送与读取，见第 7、8 节 |
| **仪表板** | 统计：哪些功能已启用、被拦截的改动、最常触发的用户、30 天走势 |
| **导入模板** | 供 NetBox 批量导入使用的可下载 CSV 模板。启用后所有已登录用户可见 |
| **使用说明** | 面向自有用户的自由文本页面。启用后所有已登录用户可见 |
| **补丁管理** | 见第 9 节 |

有两项设置值得单独一提：

- **全局开关** — 暂停所有检查，例如在维护窗口期间。
- **试运行模式（dry-run）** — 记录违规但不拦截任何操作。这是引入新规则的正确方式：
  在真正拦住任何人之前，先看清哪些操作*本会*被拦截。

---

## 7. Graylog — 发送

通过 GELF 把审计事件从 NetBox 发往 Graylog。

### 为何需要

有三样东西在 NetBox 的其他任何地方都没有记录：

- **失败的登录。** NetBox 根本不保存。
- **改动的来源 IP 与浏览器标识。** NetBox 的变更日志两者都不携带。
- **插件自身设置的改动。** 它们不在 NetBox 的变更日志范围内——谁关闭了强制校验，此前
  不会在任何地方留下痕迹。

### 配置

在 **Graylog** 页面上半部分：主机、端口、传输方式。然后点击*发送测试事件*。

先用 **UDP**。如果什么都没收到，改用 **TCP**——UDP 从设计上无法报告失败，TCP 可以。
这能区分「端口不对」与「消息被丢弃」。

| 传输方式 | 确认送达 | 加密 |
|---|---|---|
| UDP | 否 | 否 |
| TCP | 是 | 否 |
| TCP + TLS | 是 | 是 |
| HTTP | 是 | 否 |
| HTTPS | 是 | 是 |

UDP 在局域网内是合适的，跨互联网则不合适。

### 发送哪些内容

每类事件一行，各带一个复选框和 syslog 严重级别：对象创建、修改、删除；登录；登出；
登录失败；被拦截的改动；插件设置已更改。

### 数量

一次请求若修改的对象超过所设阈值，将作为**一条汇总事件**上报。导入 500 台设备是一次
操作——500 条几乎相同的日志只会让它更难被发现，而不是更容易。

选择汇总而非限流是有意为之。一个排空比填入更慢的队列，丢弃的是*最新*的事件，也就是
恰恰不该丢的那一半。

### 字段名称

每条事件都携带相同的字段，使检索保持简单：

```
_app          netbox_force
_category     object_change | auth | violation | settings
_event        object_created, login_failed, …
_username
_client_ip
_user_agent
_object_type  dcim.device
_object_id
_object_name
_action       create | update | delete
_changed_fields
_request_id
_netbox_url
_outside_business_hours
```

`_request_id` 把一次请求所改动的一切归为一组。一次批量编辑四十台设备是一次操作，
而不是四十个谜题。

### 需要知道的三点

- **Graylog 故障既不会拖慢 NetBox 的保存，也不会导致保存失败。** 事件进入一个有上限的
  队列，由后台线程发送。队列满时新事件会被丢弃并计数，计数显示在页面上。
- **消息正文始终为英文**，与界面语言无关。Graylog 的告警查询依赖这段文本；一旦有人
  改动界面语言，翻译过的文本会让所有告警悄然失效。
- **客户端 IP 在存在时取自 `X-Forwarded-For`。** 该头部由客户端提供，若 NetBox 前面
  没有反向代理即可访问，它是可以伪造的。

---

## 8. Graylog — 读取

把 Graylog 的信息带进 NetBox，使人无需另开一个标签页即可判断某台主机的状况。

### 配置

**Graylog** 页面下半部分：Web 地址与 API 令牌，然后点击*测试连接*。结果会给出 Graylog
版本、识别出的搜索 API 形式、消息最多的来源以及可用的流。*立即轮询*会马上执行一次
轮询。

**请为具有只读角色的 Graylog 用户签发令牌。** 真正保证无法从 NetBox 修改 Graylog 的
是这个角色，而不是本插件的代码。

### 这里的「只读」究竟指什么

每次调用要么获取数据，要么请求 Graylog 执行一次搜索。旧的搜索端点是纯 `GET`。较新的
Views 搜索 API 则不是：它需要一次 `POST` 注册搜索，再一次 `POST` 执行。这会在 Graylog
内部产生一个短暂的搜索对象并返回结果，不会改动已存储的数据。若贵方环境只接受 `GET`，
请在设置中把搜索形式固定为 `legacy`。

### 把来源与 NetBox 对象关联

精确匹配，按此顺序，首个命中即生效：

| | 规则 |
|---|---|
| 1 | **手动关联** — 一经设定，始终优先 |
| 2 | **IP 地址** — 来源与该对象的所有 IP 比对 |
| 3 | **主机名**，不区分大小写 |
| 4 | **去掉所配置域名后缀之后的主机名** |

其余一律保持未关联，并如实列出。

**此处刻意不做模糊匹配。** `srv-web-01` 与 `srv-web-02` 只差一个字符，任何相似度算法
都会判定它们 96 % 一致，然而这是两台不同的机器。在带编号的命名方案中——也就是在任何
称得上 NetBox 的系统里——最相似的候选往往正是错误的那台。日志会被归到邻近服务器名下，
而没有人会察觉。相似度仅用于**排序**未关联来源旁的候选建议，绝不会自行完成关联。

若 Graylog 前面有集中式 syslog 转发器，所有消息都会带上转发器的地址，规则 2 就找不到
有用的匹配。此时来源字段必须携带主机名，规则 3 和 4 正是为此而设。

### 各页面

- **来源** — Graylog 报告的一切，带计数，可按已关联、未关联、静默、从未出现和已忽略
  筛选。
- **静默** — 在 NetBox 中已关联但不再发送任何内容。可能是已停机、日志配置损坏，或是
  残留条目。两个系统各自都发现不了这一点。
- **从未在 Graylog 中出现** — 交叉核对的另一半。
- **集群** — 带绿/黄/红指示灯的节点、索引器健康状况、日志积压，每个节点都链接到其在
  NetBox 中的虚拟机。
- **在对象上** — 已关联来源的设备和虚拟机会获得一个 Graylog 面板，含计数、按需查看的
  最近消息以及跳转 Graylog 的链接。

### 负载与安全

- 一次轮询是**针对所有主机的一条分组查询**，而非每台设备一条查询。800 台设备的站点
  只需三次请求。
- 集群面板与消息列表在页面渲染**之后**才加载。Graylog 缓慢或宕机只会得到空面板，绝不
  会让 NetBox 页面卡住。
- 关联关系存放在插件自有的表中。**Graylog 从不写入 NetBox 的核心对象**——卸载插件即
  移除关联，NetBox 毫发无损。
- 消息接口只对已关联到调用者有权查看的对象的来源作出响应。

---

## 9. 补丁管理与 CheckMK

按虚拟机或物理服务器记录补丁状态、操作系统、责任人和更新历史。

- **状态** 绿 / 黄 / 红，可手工维护，也可从 CheckMK 读取。
- **逾期阈值** — N 天内未打补丁的条目标记为逾期。
- **升级** — 停留在*黄色* N 天的条目会自行变为*红色*。
- **联系人** — 来自 NetBox 联系人对象的管理员与流程负责人。
- **更新历史** — 每次打补丁一条记录，含工单编号与备注。
- **访问权限**通过插件设置中的 NetBox 组名授予，而不是通过 Django 权限。

### CheckMK

该集成是 **pull**：由 NetBox 读取 CheckMK。不会向 CheckMK 写入任何内容，因此一个只读
的自动化用户即可。

在设置页面配置：站点 URL、自动化用户、密钥、服务过滤器和同步间隔。密钥加密保存，且
不再显示。

停滞的同步是最伤人的故障，因为页面会继续显示一个已悄然失真的补丁状态。因此仪表板会
直接指出：上次成功同步已早于所设间隔的两倍。

---

## 10. 故障排查

**插件没有出现在侧边栏。**
`configuration.py` 中设置了 `PLUGINS` 吗？迁移执行了吗？NetBox 重启了吗？侧边栏标签
只在重启时更新；插件内部的标签页会立即更新。

**改动没有被拦截。**
按此顺序检查：全局开关、试运行模式、该用户是否在豁免用户或豁免组中，以及是否有模型
策略为该模型关闭了强制校验。

**页面报告缺少列。**
迁移未执行，或只执行了一部分。`python manage.py migrate netbox_force`。

**「没有后台工作进程在运行。」**
`netbox-rq` 没有运行。此时 CheckMK 同步和 Graylog 轮询只在点击按钮时执行。

**Graylog 收不到任何内容。**
把传输方式从 UDP 改为 TCP。UDP 无法报告失败，TCP 可以，其错误信息会指出是端口不对
还是消息被拒绝。

**设备上的 Graylog 面板一直是空的。**
该设备没有关联来源。打开*来源 → 未关联*进行关联，或在设置中加入贵方的域名后缀，
以便 FQDN 能被缩短。

**更改 `SECRET_KEY` 之后，CheckMK 密钥或 Graylog 令牌不再可用。**
两者都用从 `SECRET_KEY` 派生的密钥加密。需要重新输入。

---

## 11. 更改语言

语言是**按安装**设置的，而不是按用户。在设置页面中更改。

插件内部的标签页和页面立即切换。侧边栏标签在启动时构建一次，只有重启 NetBox 后才会
改变。

拦截时向用户显示的消息遵循此设置。API 错误消息以及发往 Graylog 的消息保持英文——参见
[文档索引](../README.md)中的说明。

---

## 12. 许可证

AGPL-3.0。参见 [LICENSE](../../LICENSE)。
