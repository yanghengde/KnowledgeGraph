# AttachedDocs → HAS_DOC_ATTACHMENTS → DocAttachments

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[AttachedDocs]`（别名 `src`）
- 目标表：`[DocAttachments]`（别名 `tgt`）
- JOIN 条件：`src.[DocAttachmentsId] = tgt.[DocAttachmentsId]`
- 物理外键：`[AttachedDocs].[DocAttachmentsId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [AttachedDocs] AS src
LEFT JOIN [DocAttachments] AS tgt
    ON src.[DocAttachmentsId] = tgt.[DocAttachmentsId]
WHERE src.[AttachedDocId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`AttachedDocs --[HAS_DOC_ATTACHMENTS]--> DocAttachments`
- 基数：`MANY_TO_ONE`
- 物理定义：`AttachedDocs.DocAttachmentsId`
- 源表主键：`AttachedDocs.AttachedDocId`
- 目标表主键：`DocAttachments.DocAttachmentsId`
