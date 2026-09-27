# 访问统计与内网监控

博客继续由 `serve.py` 提供静态页面，同时暴露同源统计接口。将 `serve.py` 和 `analytics.py` 放在博客服务根目录，`data/` 自动创建，数据库与匿名化密钥必须一起备份并留在服务器，不能上传到 Git。统计从本次启用时开始，只保留近 90 天。访客/阅读人数按匿名 IP 去重估算，页面访问按 30 分钟去重；DNT/GPC 和常见机器人不计入。

`monitor.py`、`monitor.html` 和 `analytics.py` 同目录运行：

```sh
python3 monitor.py --blog-root /path/to/blog --port 8765
```

局域网通过 `http://<手机LAN地址>:8765/` 查看汇总。8765 不加入隧道，按真实私网来源、Host 和 Origin 限制访问，并拒绝代理请求头。局域网设备可看脱敏网段统计，无完整 IP 或房间个人数据；共享 Wi-Fi 中其他设备也可能访问此页。CPU/内存/温度等数据取决于 Android 文件权限，缺失显示不可用。手机网络切换后使用新的 LAN 地址。

全机 CPU 不可读时，尝试读取本站进程的 CPU 时间，页面明确标记为“本站服务 CPU”，占用率按全机核心容量归一化，不把它当作系统总占用率。运行时长优先读取 `/proc/uptime`，Android 限制读取时使用内核 BOOTTIME 时钟。温度缺失时保持不可用。

## Ledger 适配

在**新的 release 副本**执行，避免更改运行中的源码：

```sh
python3 install-ledger-metrics.py /path/to/new-ledger-release
```

只增加两处只读统计方法、内部监听模块及入口调用，8788 仅绑定 `127.0.0.1`。重新启动房间服务会清空内存房间，发布前确认允许中断。源码安装有锚点验证且可重复执行，不修改本地 Ledger 仓库。在线连接只统计 readyState=OPEN 的房间连接。

## Termux 发布

本地先执行 `npm run check`、`SITE_URL=<公开域名> npm run build`、`npm test`、`npm run test:server`。归档只包括 `dist`、`deploy`、`tests`，不包括 `.env`、数据库或密钥。将归档上传到服务器，再使用归档中的 `deploy/publish.py <归档路径>`。发布工具先验证新房间服务副本、保留旧 release 和 runtime，再切换并重启，失败尝试恢复旧版本。新增 `20-zuoer-monitor` 使用独立启动锁，保留 `10-zuoer-server`。验证两个启动脚本重复执行不会增加服务进程。

成功发布的目录里 `rollback.json` 记录旧版本位置，`previous-runtime/` 保存旧服务脚本。手工回退时先停止这次启动的相关进程，恢复运行脚本及 `current` 链接，再执行既有开机脚本；不要删除 `data/`。

## Giscus

需要 GitHub 仓库开启 Discussions、安装 Giscus GitHub App，并选定公告分类。将仓库 ID、分类 ID 写入本机 `.env` 的四项 `PUBLIC_GISCUS_*` 配置后构建发布。这些 ID 为公开嵌入配置，访问令牌不得写入代码。评论仍由读者主动点击加载。
