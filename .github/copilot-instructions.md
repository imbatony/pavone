# Copilot Instructions for PAVOne

在执行任何任务前，必须读取并遵守仓库根目录的 [`AGENTS.md`](../AGENTS.md)。`AGENTS.md` 是架构、代码质量、
测试、PR 标题、发布标签和 Release Notes 的唯一规范源。

创建或更新 PR 时，必须使用 Conventional Commits 标题，保留 PR 模板中的 release-notes 标记，并在标记内填写
中文、面向用户的变更；没有用户可感知变化时添加 `release:skip` 标签。不要在普通 PR 中手动递增版本或创建
CHANGELOG 版本条目。
