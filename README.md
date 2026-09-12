# GitUploader

GitUploader 是一个运行在 Termux 中的 Git 上传命令生成工具。

你可以按项目创建多个“仓库”，再为每个仓库保存多套命令模板。模板中的固定命令保持不变，日期、时间、用户名等实时内容会在使用时自动替换。

## 安装

### 从 GitHub Release 安装

配置 Termux交流社区 镜像源，然后在 Termux 中执行：

```bash
apt update
apt install ./gituploader_1.0.4_all.deb
gitup -h
```

安装完成后，如果能看到帮助信息，就表示安装成功。

### 从 APT 镜像安装

如果软件已经发布到 APT 镜像，可以直接安装：

```bash
apt update
apt install gituploader
gitup -h
```

### 从 Python 安装

```bash
pip install gituploader
gitup -h
```

## 快速开始

### 直接打开交互菜单

不带参数运行 `gitup` 会打开交互菜单，适合第一次使用或不熟悉命令时操作：

```bash
gitup
```

菜单支持创建仓库、查看仓库、添加模板、查看模板、生成命令和执行模板。输入 `0` 可以退出菜单。

### 使用命令直接操作

如果输入了具体命令，GitUploader 会直接执行，不会打开交互菜单。

```bash
gitup repo create myproject
gitup template list myproject
gitup gen myproject daily
```

### 1. 创建仓库

```bash
gitup repo create myproject
```

`myproject` 是 GitUploader 中保存命令模板的仓库名称。

查看已有配置：

```bash
gitup repo list
```

### 2. 创建命令模板

```bash
gitup template add myproject daily "git add . && git commit -m 'Update {date}' && git push"
```

查看某个项目的全部模板：

```bash
gitup template list myproject
```

一个项目可以保存多套模板，例如：

```bash
gitup template add myproject commit "git add . && git commit -m 'Update {date} {time}'"
gitup template add myproject release "git add . && git commit -m 'Release {year}.{month}.{day}' && git push --tags"
```

在交互菜单中添加模板时支持多行命令：逐行输入或粘贴命令，最后单独输入 `END` 保存。例如：

```text
git add .
git commit -m "Update {date}"
git push
END
```

添加模板时，菜单会显示可用占位符：`{date}`、`{time}`、`{datetime}`、`{year}`、`{month}`、`{day}`、`{timestamp}`、`{username}`、`{hostname}`。

### 3. 生成当前命令

```bash
gitup gen myproject daily
```

该命令只输出替换完成后的命令，不会自动执行。你可以先检查输出，再复制到当前 Git 项目目录执行。

### 4. 执行模板

```bash
gitup run myproject daily
```

执行前请确认当前目录是正确的 Git 项目目录，并确认模板命令内容可信。

## 实时占位符

模板中可以自由组合以下占位符：

| 占位符 | 生成内容示例 |
| --- | --- |
| `{date}` | `2026-09-11` |
| `{time}` | `14:30:05` |
| `{datetime}` | `2026-09-11 14:30:05` |
| `{year}` | `2026` |
| `{month}` | `09` |
| `{day}` | `11` |
| `{timestamp}` | `20260911143005` |
| `{username}` | 当前用户名 |
| `{hostname}` | 当前设备名称 |

例如：

```bash
gitup template add myproject daily "git add . && git commit -m 'Update {date} {time}' && git push"
```

GitUploader 也兼容以下旧格式：`%Y-%m-%d`、`%H:%M:%S`、`%username`、`%hostname`。

## 数据保存位置

模板数据默认保存在：

```text
~/.gituploader/
```

请定期备份该目录，以免丢失自己的模板配置。

## GitHub 自动构建

项目发布新版本时，GitHub Actions 会自动构建 Python 安装包和 Termux/Debian `.deb` 安装包。

如果只是推送普通代码，Actions 只进行编译检查，不会创建下载页面。要得到可直接下载的 `.deb`，有两种方式：

1. 推送版本标签，自动创建 Release：

```bash
git tag v1.0.4
git push origin v1.0.4
```

2. 在 GitHub 的 `Actions -> Build GitUploader -> Run workflow` 中勾选 `publish_release`，填写 `release_tag`，然后运行。

构建成功后打开 `Releases -> Assets`，只下载文件名以 `.deb` 结尾的文件：

```text
gituploader_1.0.4_all.deb
```

不要点击 `Source code (zip)`，它是 GitHub 自动生成的源码压缩包，不是安装包。

发布新版本：

```bash
git add .
git commit -m "Release gituploader 1.0.4"
git push origin main
git tag v1.0.4
git push origin v1.0.4
```

请从 GitHub Release 页面 Assets 中下载真正的 `.deb` 文件，例如：

```text
gituploader_1.0.4_all.deb
```

工作流只将 `.deb` 发布为 Release Asset。`.deb` 是 Debian 安装包，不能用解压软件判断其内容，请直接安装：

```bash
apt install ./gituploader_1.0.4_all.deb
```

## 获取帮助

```bash
gitup -h
gitup repo -h
gitup template -h
gitup gen -h
```
