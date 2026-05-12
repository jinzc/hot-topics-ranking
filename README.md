# 🔥 全网热点榜单

> 实时聚合微博、百度、知乎、抖音、B站等主流平台热搜数据，每小时自动更新

## 🌐 在线访问

**GitHub Pages 地址**: `https://你的用户名.github.io/hot-topics-ranking/`

## 📁 项目结构

```
hot-topics-ranking/
├── index.html                 # 主页面（前端展示）
├── data/
│   └── hot_data.json         # 热点数据（每小时自动更新）
├── scripts/
│   └── update_hot_topics.py  # 数据抓取脚本
├── .github/
│   └── workflows/
│       └── update.yml        # GitHub Actions 自动更新配置
└── README.md                 # 项目说明
```

## 🚀 快速开始

### 1. Fork 或创建仓库

- 在 GitHub 创建名为 `hot-topics-ranking` 的公开仓库
- 将本项目的所有文件上传到新仓库

### 2. 开启 GitHub Pages

1. 进入仓库 **Settings** → **Pages**
2. **Source** 选择 **Deploy from a branch**
3. **Branch** 选择 `main` / `root`
4. 点击 **Save**
5. 等待 1-2 分钟，访问 `https://你的用户名.github.io/hot-topics-ranking/`

### 3. 自动更新已配置完成

- 每小时自动运行 `scripts/update_hot_topics.py` 抓取最新热点
- 自动提交更新到 `data/hot_data.json`
- 前端页面每 5 分钟自动刷新数据

## 📊 数据来源

| 平台 | 链接 | 状态 |
|------|------|------|
| 微博热搜 | https://weibo.com/a/hot/realtime | ✅ 已接入 |
| 百度热搜 | https://top.baidu.com/board | ✅ 已接入 |
| 知乎热榜 | https://rebang.today/ | ✅ 已接入 |
| 抖音热榜 | - | 🔄 待接入 |
| B站热搜 | - | 🔄 待接入 |

## 🛠️ 本地开发

```bash
# 克隆仓库
git clone https://github.com/你的用户名/hot-topics-ranking.git
cd hot-topics-ranking

# 安装依赖
pip install requests beautifulsoup4

# 手动运行更新脚本
python scripts/update_hot_topics.py

# 启动本地服务器预览
python -m http.server 8000
# 访问 http://localhost:8000
```

## ⚙️ 自定义配置

### 修改更新频率

编辑 `.github/workflows/update.yml` 中的 cron 表达式：

```yaml
# 每小时更新（默认）
- cron: '0 * * * *'

# 每30分钟更新
- cron: '0,30 * * * *'

# 每天早8点更新
- cron: '0 8 * * *'
```

### 添加新的数据源

在 `scripts/update_hot_topics.py` 中添加新的抓取函数：

```python
def fetch_douyin_hot():
    """抓取抖音热榜"""
    # 实现抓取逻辑
    pass
```

然后在 `merge_topics()` 函数中接入新数据。

## 📱 分享方式

部署完成后，你可以通过以下方式分享：

- **直接链接**: `https://你的用户名.github.io/hot-topics-ranking/`
- **二维码**: 使用任意二维码生成器将链接转为二维码
- **嵌入网页**: `<iframe src="https://你的用户名.github.io/hot-topics-ranking/" width="100%" height="800"></iframe>`

## 🤝 贡献

欢迎提交 Issue 和 PR：
- 添加新的数据源
- 优化前端样式
- 改进分类算法
- 修复抓取脚本

## 📄 许可

MIT License
