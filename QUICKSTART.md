# BrowserUse Agent Helper - 快速开始

## 快速验证

### 1. 验证安装

```bash
cd browseruse-cdp-best-practise
uv run python -c "from src import SimpleBrowserManager, tools; print('✅ 导入成功！')"
```

### 2. 运行测试 1（网络数据捕获）

**终端 1：启动 API 服务器**
```bash
cd browseruse-cdp-best-practise
uv run python tests/api_server.py
```

**终端 2：运行测试**
```bash
cd browseruse-cdp-best-practise
uv run python tests/test_1_improved.py
```

### 3. 运行测试 2（Tab 管理）

```bash
cd browseruse-cdp-best-practise
uv run python tests/test_2_simple.py
```

### 4. 运行测试 3（DOM 可见性）

确保 API 服务器正在运行，然后：

```bash
cd browseruse-cdp-best-practise
uv run python tests/test_3.py
```

## 项目结构

```
browseruse-cdp-best-practise/
├── src/
│   ├── __init__.py              # 包入口
│   ├── browser_manager.py       # 浏览器管理器（CDP集成）
│   └── tools.py                 # BrowserUse 自定义工具
├── tests/
│   ├── test_1_improved.py       # 网络数据捕获测试
│   ├── test_2_simple.py         # Tab 管理测试
│   ├── test_3.py                # DOM 可见性测试
│   ├── test_page.html           # 测试页面
│   └── api_server.py            # 测试 API 服务器
├── .env                         # 环境变量配置
├── .env.example                 # 环境变量示例
├── pyproject.toml               # 项目配置
└── README.md                    # 详细文档
```

## 环境配置

已从主项目复制 `.env` 文件。如果需要修改，编辑 `browseruse-cdp-best-practise/.env`：

```env
GEMINI_API_KEY=your_api_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL=gemini-2.0-flash-exp
```

## 核心功能

### 1. 浏览器管理器
- 通过 CDP 启动和连接 Chrome
- Playwright 和 BrowserUse 共享同一浏览器实例
- 网络事件监听和数据捕获

### 2. 自定义工具
- `get_network_data(keyword)`: 获取网络请求数据
- `is_dom_visible(dom_id)`: 检查 DOM 元素可见性
- `mark_initial_tab()`: 标记初始标签页
- `open_in_new_tab(url)`: 在新标签页打开链接
- `close_tabs_and_return()`: 关闭其他标签页并返回

## 常见问题

### Q: 如何验证项目正常工作？
A: 运行 `uv run python -c "from src import SimpleBrowserManager, tools; print('✅ 成功！')"`

### Q: 测试失败怎么办？
A:
1. 确保 API 服务器正在运行（测试 1 和 3）
2. 检查 .env 文件中的 API 密钥是否正确
3. 查看终端输出的错误信息

### Q: 如何添加新工具？
A: 在 `src/tools.py` 中使用 `@tools.action` 装饰器添加新函数

## 下一步

1. 查看详细文档：`README.md`
2. 研究测试代码了解具体用法
3. 根据需求扩展自定义工具
4. 集成到自己的项目中
