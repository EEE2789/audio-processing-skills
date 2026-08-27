# 错误反省记录 - generate-cover-v2

## 2026-03-11：`--title` 参数格式错误

### 错误场景
用户要求生成标题为"反抽加空单"的封面。

### 错误操作
```bash
python generate_cover.py --auto --title "反抽加空单"
```

### 问题原因
- 脚本只识别 `--title=xxx` 格式（等号连接）
- `--title "xxx"` 格式会被解析为两个独立参数：
  - `--title` - 不匹配任何已知参数，被忽略
  - `"反抽加空单"` - 不是 .txt 文件、不是颜色、不是日期，被跳过
- 结果：脚本使用了 AI 生成的标题而非用户指定的标题

### 正确操作
```bash
python generate_cover.py --auto --title="反抽加空单"
```

### 教训
1. **传递用户指定标题时，必须使用 `--title=标题` 格式（等号，无空格）**
2. 执行后检查输出中的 `📝 使用指定标题:` 确认标题是否被正确使用
3. 不要假设参数格式，第一次执行时验证输出是否符合预期
4. 如果输出显示 `🤖 自动模式：已选择第1个标题:` 而非 `📝 使用指定标题:`，说明参数格式错误

### 代码位置
脚本参数解析逻辑在 `generate_cover.py` 第 498-504 行：
```python
for i, arg in enumerate(sys.argv[1:]):
    if arg.startswith('--title='):
        custom_title = arg.split('=', 1)[1]
        break
```

只检查 `--title=` 前缀，不处理 `--title "xxx"` 格式。
