# 全网热点榜单

> 实时聚合微博、百度、知乎等主流平台热搜数据，每小时自动更新
>
> 支持部署到 **Gitee Pages**（国内访问更快）

## 在线访问

部署完成后，你的访问地址将是：

```
https://你的用户名.gitee.io/hot-topics-ranking
```

## 项目结构

```
hot-topics-ranking/
├── index.html                 # 主页面（前端展示）
├── data/
│   └── hot_data.json         # 热点数据（每小时自动更新）
├── scripts/
│   └── update_hot_topics.py  # 数据抓取脚本
├── .github/
│   └── workflows/
│       └── update.yml        # GitHub Actions 自动更新配置（备用）
├── README.md                 # 项目说明
```

## Gitee 部署完整步骤

### 第一步：注册 Gitee 账号

1. 打开 [gitee.com](https://gitee.com)
2. 点击右上角 **注册**，用手机号或邮箱注册账号
3. 完成实名认证（部署 Pages 需要实名认证）

### 第二步：创建仓库

1. 登录后点击右上角 **+** -> **新建仓库**
2. 填写仓库信息：
   - **仓库名称**：`hot-topics-ranking`（建议和用户名一致）
   - **仓库介绍**：全网热点榜单 - 实时聚合多平台热搜数据
   - **是否开源**：选择 **公开**（必须公开才能开启 Pages）
   - **初始化仓库**：勾选 **使用Readme文件初始化**
3. 点击 **创建**

> **重要提示**：Gitee Pages 免费版要求仓库名必须和用户名一致才能使用根目录部署。如果你的用户名是 `zhangsan`，仓库名必须是 `zhangsan`，访问地址就是 `zhangsan.gitee.io`。如果仓库名不同，访问地址会带上仓库名路径。

### 第三步：上传文件

#### 方法 A：Git 命令行（推荐）

```bash
# 1. 下载本项目的 zip 文件并解压
cd hot-topics-ranking

# 2. 初始化 git
git init

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "Initial commit: hot topics ranking"

# 5. 关联 Gitee 远程仓库（把 你的用户名 替换成实际的）
git remote add origin https://gitee.com/你的用户名/hot-topics-ranking.git

# 6. 推送到 Gitee
git branch -M master
git push -u origin master
```

#### 方法 B：网页上传（适合新手）

1. 进入 Gitee 仓库页面
2. 点击 **文件** -> **上传文件**
3. 把解压后的文件拖进去，逐个上传：
   - `index.html`
   - `data/hot_data.json`
   - `scripts/update_hot_topics.py`
   - `.github/workflows/update.yml`
4. 每次上传填写提交信息

> 注意：Gitee 网页上传不支持直接上传文件夹，你需要：
> - 先创建文件夹（点击 **+** -> **新建文件**，路径写 `scripts/update_hot_topics.py`）
> - 或者使用 Gitee 的 **Web IDE**（点击 **Web IDE** 按钮，可以批量上传）

### 第四步：开启 Gitee Pages

1. 进入仓库 -> **服务** -> **Gitee Pages**
2. 部署来源选择 **master 分支**
3. 部署目录选择 **/**
4. 点击 **启动**
5. 等待 1-2 分钟，会显示你的访问链接：
   ```
   https://你的用户名.gitee.io/hot-topics-ranking
   ```

### 第五步：验证部署

打开上面的链接，你应该能看到热点榜单页面。如果看到空白或 404：
- 检查 `index.html` 是否在仓库根目录
- 检查 Gitee Pages 是否已启动（状态显示"已开启"）
- 等待 2-3 分钟再刷新（Gitee Pages 有缓存）

## 自动更新方案（Gitee 限制说明）

### Gitee 的 Actions 限制

Gitee 的 **Gitee Go**（类似 GitHub Actions）是收费功能，免费用户无法使用自动定时任务。

### 替代方案：手动更新 + 本地定时

#### 方案 1：本地电脑定时运行（Windows）

1. 安装 Python：[python.org](https://python.org)
2. 安装依赖：
   ```bash
   pip install requests beautifulsoup4
   ```
3. 创建 Windows 批处理文件 `update.bat`：
   ```batch
   @echo off
   cd /d C:\你的路径\hot-topics-ranking
   python scripts\update_hot_topics.py
   git add data\hot_data.json
   git commit -m "Update hot topics"
   git push origin master
   ```
4. 打开 **任务计划程序** -> 创建基本任务：
   - 名称：`Update Hot Topics`
   - 触发器：每小时
   - 操作：启动程序 `update.bat`

#### 方案 2：本地电脑定时运行（Mac/Linux）

```bash
# 编辑 crontab
crontab -e

# 添加一行（每小时运行一次）
0 * * * * cd /你的路径/hot-topics-ranking && python scripts/update_hot_topics.py && git add data/hot_data.json && git commit -m "Update" && git push origin master
```

#### 方案 3：使用 GitHub 做自动更新，Gitee 只做展示

1. 在 **GitHub** 创建同名仓库，开启 GitHub Actions 自动更新
2. 在 Gitee 仓库 -> **管理** -> **仓库镜像管理** -> **添加镜像**
3. 选择 **GitHub** -> 授权 -> 选择你的仓库
4. 开启 **自动同步**（每小时或每天同步一次）
5. 这样 GitHub 自动更新数据，Gitee 自动同步展示

#### 方案 4：使用云服务器/云函数（最稳定）

- **阿里云函数计算**：创建定时触发器，每小时运行脚本
- **腾讯云云函数**：同上
- **华为云 FunctionGraph**：同上

脚本逻辑：
1. 运行 `update_hot_topics.py` 生成新数据
2. `git push` 到 Gitee 仓库
3. Gitee Pages 自动部署最新版本

## 数据来源

| 平台 | 链接 | 状态 |
|------|------|------|
| 微博热搜 | https://weibo.com/a/hot/realtime | 已接入 |
| 百度热搜 | https://top.baidu.com/board | 已接入 |
| 知乎热榜 | https://rebang.today/ | 已接入 |
| 抖音热榜 | - | 待接入 |
| B站热搜 | - | 待接入 |

## 本地开发

```bash
# 克隆仓库
git clone https://gitee.com/你的用户名/hot-topics-ranking.git
cd hot-topics-ranking

# 安装依赖
pip install requests beautifulsoup4

# 手动运行更新脚本
python scripts/update_hot_topics.py

# 启动本地服务器预览
python -m http.server 8000
# 访问 http://localhost:8000
```

## 分享方式

部署完成后，你的链接格式：

```
https://你的用户名.gitee.io/hot-topics-ranking
```

分享方式：
- 微信/QQ 直接发链接
- 生成二维码分享
- 嵌入到其他网页

## Gitee vs GitHub 对比

| 功能 | Gitee | GitHub |
|------|-------|--------|
| 国内访问速度 | 快 | 较慢（需翻墙） |
| Pages 免费版 | 有 | 有 |
| Actions 免费版 | 收费 | 免费 |
| 仓库名要求 | 需和用户名一致 | 无要求 |
| 自动更新 | 需额外配置 | 原生支持 |

**建议**：国内用户用 Gitee 做展示，GitHub 做自动更新，通过镜像同步。

## 贡献

欢迎提交 Issue 和 PR：
- 添加新的数据源
- 优化前端样式
- 改进分类算法
- 修复抓取脚本

## 许可

MIT License
