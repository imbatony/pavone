## 变更概述

<!-- 说明为什么修改、解决了什么问题，以及主要实现方式。 -->

## Release Notes

<!--
仅填写用户可感知的变化，删除不需要的小节。
允许的小节：新增、修复、改进、重大变更、变更；每项必须以 "- " 开头。
没有用户可感知变化时保持区块为空，并添加 release:skip 标签。
不要删除下面两个 release-notes 标记。
-->

<!-- release-notes:start -->

<!-- release-notes:end -->

## 验证

<!-- 列出实际执行的测试、静态检查或人工验证。 -->

- [ ] 已完成与改动对应的验证
- [ ] 已添加或更新必要测试

## 关联事项

<!-- 使用 Fixes #123、Closes #456 或 Related to #789。没有则填写“无”。 -->

## 发布级别

版本默认由 PR 标题推断：`feat` → minor，`!`/`BREAKING` → major，其余 → patch。

<!--
仅在需要覆盖自动推断时添加一个标签：
release:major / release:minor / release:patch / release:skip
-->

## 提交前检查

- [ ] PR 标题符合 `type(scope)!: description`
- [ ] Release Notes 使用中文描述用户可感知变化，或已添加 `release:skip`
- [ ] major 变更包含 `### 重大变更` 和迁移说明
- [ ] 未手动修改版本号或新增 CHANGELOG 版本条目
