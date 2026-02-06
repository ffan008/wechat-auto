# 贡献指南

感谢您对本项目的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了bug或有功能建议：

1. 检查 [Issues](https://github.com/ffan008/wechat-auto/issues) 中是否已存在相同问题
2. 如果没有，创建新的Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤（如果是bug）
   - 预期行为
   - 环境信息（Python版本、操作系统等）
   - 相关日志或截图

### 提交代码

1. **Fork本仓库**
   ```bash
   # 在GitHub上点击Fork按钮
   ```

2. **克隆到本地**
   ```bash
   git clone https://github.com/YOUR_USERNAME/wechat-auto.git
   cd wechat-auto
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行修改**
   - 遵循现有代码风格
   - 添加必要的测试
   - 更新相关文档

5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加XXX功能"
   ```

   提交信息格式：
   - `feat:` 新功能
   - `fix:` Bug修复
   - `docs:` 文档更新
   - `style:` 代码格式
   - `refactor:` 重构
   - `test:` 测试相关
   - `chore:` 构建/工具

6. **推送到GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建Pull Request**
   - 访问原仓库
   - 点击"New Pull Request"
   - 填写PR描述
   - 等待review

## 📋 代码规范

### Python代码风格

- 使用 `black` 格式化代码
- 使用 `isort` 排序imports
- 遵循 PEP 8 规范
- 添加类型提示
- 编写docstring

### 提交规范

使用清晰的提交信息：

```
<type>(<scope>): <subject>

<body>

<footer>
```

示例：
```
feat(chat): 添加多轮对话上下文记忆功能

- 在Redis中保存对话历史
- 实现上下文窗口管理
- 添加相关测试用例

Closes #123
```

## 🧪 测试

在提交PR前，请确保：

1. 所有测试通过
   ```bash
   pytest tests/
   ```

2. 代码格式正确
   ```bash
   black src/
   isort src/
   ```

3. 没有类型错误
   ```bash
   mypy src/
   ```

## 📝 文档

如果您的更改影响了功能，请更新相关文档：
- README.md
- QUICKSTART.md
- 代码中的docstring
- API文档

## 🎯 优先贡献领域

我们特别欢迎以下方向的贡献：

- [ ] Web管理界面
- [ ] 单元测试覆盖率提升
- [ ] 文档完善
- [ ] 性能优化
- [ ] 新Agent实现
- [ ] 国际化支持

## 💬 交流

- 提交Issue讨论问题
- 参与PR review
- 分享使用经验

## 📄 许可证

提交代码即表示您同意将代码以MIT许可证发布。

---

**再次感谢您的贡献！** 🎉
