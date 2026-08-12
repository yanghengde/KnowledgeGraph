# ZIF 出站目标建模说明 / ZIF Outbound Destination Modeling

## 中文

`zifOutboundDestination` 表示 ZIF 出站消息的目标端配置。该节点保存目标 URL、超时、传输方式、服务器列表等配置，并作为 `Factory.zifDefaultOutboundDestinatio` 的导航目标。

字段与类型严格来自 `Database_Fields.csv`。物理外键按 Navigation 建模；未被 CSV 标记为外键的字段保持普通数据属性。

## English

`zifOutboundDestination` represents the destination configuration for ZIF outbound messaging. It stores the URL, timeout, transport, and server-list settings and is the navigation target of `Factory.zifDefaultOutboundDestinatio`.

Field names and types follow `Database_Fields.csv`; only declared physical foreign keys are modeled as Navigation properties.
