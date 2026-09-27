---
title: 旧 Android 手机搭个服务器
description: Termux 管连接，Debian 跑应用，Cloudflare Tunnel 接公网。记录工具、命令和容易踩的坑。
date: 2026-09-27
tags: [Android, Termux, Engineering]
draft: false
sample: false
---

手里有台闲置 Android 手机，拿来跑博客、Demo 和小 API，够做一个实验服务器。这份备忘录整理工具、步骤、踩坑和资源，不刷机，不要求 Root。

左二博客最初直接跑在 Termux 中，从局域网验证。下面记录的是包含 Debian 和 Cloudflare Tunnel 的扩展方案，命令使用示例配置，不作本站当前部署状态说明。

## 工具与分工

| 工具 | 放在哪里 | 用途 |
|---|---|---|
| Termux | Android | 命令行宿主环境 |
| OpenSSH | Termux | 从电脑管理手机 |
| PRoot Distro | Termux | 运行 Debian 用户空间 |
| Debian | PRoot 环境 | 需要 Linux 发行版依赖的应用 |
| cloudflared | Termux | 连接 Cloudflare Tunnel |
| tmux | Termux | 保留终端会话 |

```text
Internet
   ↓
Cloudflare Tunnel
   ↓
Termux
   ├── SSH / cloudflared / tmux
   └── Debian（可选）
        └── Web :8080
```

Termux 管连接和会话，Debian 提供应用依赖。静态博客能直接在 Termux 运行，就不必多套一层 Debian。PRoot 与 Android 共享内核，也不提供虚拟机级别的隔离，见 [PRoot Distro 官方说明](https://github.com/termux/proot-distro)。

## 步骤

### 1. 连上手机

在 Termux 中安装工具并启动 SSH：

```bash
pkg update
pkg install git curl openssh tmux proot-distro
sshd
whoami
```

电脑连接，用户名用 `whoami` 的输出：

```bash
ssh -p 8022 <USER>@<PHONE_IP>
```

配置 SSH 公钥认证。手机的电池设置里允许 Termux 后台运行，具体选项随厂商系统不同。

### 2. 跑通局域网 Web

需要 Debian 时，在 Termux 执行：

```bash
proot-distro install debian
proot-distro login debian
```

进入 Debian 后：

```bash
apt update
apt install -y curl git python3 build-essential
mkdir -p /srv/www
printf '<h1>Android Server Works!</h1>\n' > /srv/www/index.html
cd /srv/www
python3 -m http.server 8080 --bind 0.0.0.0
```

同一局域网的电脑打开 `http://<PHONE_IP>:8080`。先把这一步跑通，再处理公网入口。

`http.server` 只用于验证连通性，不作为公网生产服务。不要从包含密钥或私人文件的目录启动它。

### 3. 临时 Tunnel 验证

回到 Termux，安装并启动：

```bash
pkg install cloudflared
cloudflared tunnel --url http://127.0.0.1:8080
```

终端会输出一个随机的 `https://xxxxx.trycloudflare.com` 地址。能打开页面，说明 Tunnel 到本地服务的链路已接通。

这个地址会把服务暴露到公网。只拿无敏感数据的测试页面验证；[Quick Tunnel 官方说明](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)将它定位为测试和开发用途，不保证可用性。

### 4. 固定域名

以下采用本地管理的 Tunnel，命令都在 Termux 执行。先把域名接入 Cloudflare DNS，等待状态变为 Active。

```bash
cloudflared tunnel login
cloudflared tunnel create home-server
```

按命令输出找到 UUID 和凭据 JSON 路径，在 Termux 的 `~/.cloudflared/config.yml` 中填写：

```yaml
tunnel: <TUNNEL_UUID>
credentials-file: <ABSOLUTE_CREDENTIAL_FILE_PATH>

ingress:
  - hostname: blog.example.com
    service: http://127.0.0.1:8080
  - service: http_status:404
```

这里的路径必须是实际绝对路径，不能原样保留占位符。然后校验、绑定 DNS 并启动：

```bash
cloudflared tunnel ingress validate
cloudflared tunnel route dns home-server blog.example.com
cloudflared tunnel run home-server
```

登录、创建凭据和 DNS 路由的细节见 [Cloudflare 本地管理 Tunnel 文档](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/)。上线前还要替换测试 Web 服务，确认页面范围和访问权限。Tunnel 不会自动给应用增加登录保护。

## 后台运行

在 Termux 创建两个 `tmux` 会话，分别跑网站和 Tunnel：

```bash
tmux new -s blog
proot-distro login debian
cd /srv/www
python3 -m http.server 8080 --bind 0.0.0.0
```

按 `Ctrl+B`，松开，再按 `D` 脱离会话。然后创建另一个：

```bash
tmux new -s tunnel
cloudflared tunnel run home-server
```

同样脱离后，查看或重新进入：

```bash
tmux ls
tmux attach -t blog
```

需要保持唤醒时，在 Termux 执行 `termux-wake-lock`，不用时执行 `termux-wake-unlock`。它会增加耗电，也不能保证 Android 永远不杀进程。

`tmux` 不负责崩溃重启和开机启动。长期运行再考虑 Termux:Boot 与服务管理，另行验证重启恢复。手机持续供电时留意温度和电池状态。

## 坑

### 安装源连不上

PRoot Distro 不同版本的安装机制不同，别把旧版教程和新版命令混用。先看 `proot-distro --help` 和 `proot-distro install --help`。

支持本地归档的版本，可以在电脑下载可信来源、与手机架构匹配的 Debian rootfs，核对校验值后传到手机：

```bash
scp -P 8022 debian-rootfs.tar.xz <USER>@<PHONE_IP>:
```

再在 Termux 执行：

```bash
proot-distro install ./debian-rootfs.tar.xz --name debian
```

这条命令针对官方当前文档中的归档安装接口。旧版若不支持，需要按对应版本说明处理。ARM64 常见，但不要跳过设备架构核对。

### 凭据放错环境

在 Debian 中创建 Tunnel，凭据可能落在 `/root/.cloudflared/`；改到 Termux 启动时，这条路径指向的是另一个文件系统视图，就可能报 `credentials file doesn't exist`。

让 `cloudflared` 的登录、创建和运行都留在 Termux。排查时核对进程所在环境、配置文件位置和 JSON 绝对路径，不要靠反复复制凭据碰运气。

### ICMP 警告不等于 Web 失败

若日志提示 ICMP 代理权限不足，先确认是否真的需要 ICMP。普通 Web 访问应看 Tunnel 是否注册成功、源站能否响应，以及外部 URL 的实际结果，不能只凭一条警告或 `protocol=quic` 判断成功。

### 手机重启后服务没了

关闭 SSH 窗口、退出 `tmux` 会话、Android 杀进程、手机重启是不同问题。逐个验证，别把“脱离终端还能跑”当成“无人值守能恢复”。

## 资源与发布边界

- [Termux](https://termux.dev/)
- [PRoot Distro](https://github.com/termux/proot-distro)
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)
- [参考：my server is a phone now](https://seg6.space/posts/phone-server/)

域名实名、DNS 托管和 ICP 备案是不同事项。不要仅凭“用了 Cloudflare”推断合规结论；正式对外服务前，按实际部署地区、服务内容和所用基础设施确认要求。

发布文章和提交代码时，SSH 私钥、Tunnel Token、API Token、`cert.pem` 与凭据 JSON 都不进入仓库。地址、用户名和 UUID 用占位符。公网入口只指向准备公开的服务，SSH 留作管理通道。

旧手机适合实验，稳定性仍取决于 Android 后台策略、电源和网络。先让局域网服务可靠运行，再决定要不要接公网。
