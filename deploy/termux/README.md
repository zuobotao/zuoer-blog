# Termux 开机启动

适用于当前部署：博客直接在 Termux 的 8080 端口运行，Tunnel 名称为 `zuo2-home`。不依赖 Debian，不启动 Ledger 游戏及其后端。

安装与 Termux 签名兼容的 Termux:Boot，并在手机上打开一次。允许 Termux 和 Termux:Boot 后台运行，具体设置随 Android 厂商不同。

部署文件：

- `10-zuoer-server` 放在 `~/.termux/boot/`。
- `ensure-process.sh` 放在 `~/.termux/server-start/`。
- 文件权限设为 `700`。

脚本持有短期启动锁，获取 wake lock，按需启动现有 SSH、博客和 Tunnel。重复执行不多开已识别的进程，不停止现有服务。子进程不继承启动锁。Tunnel 使用手机已有配置与凭据，不复制到仓库。

手工验证：

```bash
bash ~/.termux/boot/10-zuoer-server
tail -n 20 ~/.termux/server-start/boot.log
```

测试进程启动与重复执行，在手机上运行 `test-start.sh`，与 helper 放在同一目录。测试只启动绑定 `127.0.0.1:18765` 的临时服务，结束后停止测试创建的进程。

启动日志为 `~/.termux/server-start/boot.log`，Tunnel 日志为同目录 `tunnel.log`，博客日志仍为 `~/zuoer-blog/server.log`。这不是进程监督器，服务退出后不会由此脚本自动重启；Android 强制停止应用也可能阻止后续自启。wake lock 会增加耗电，日志需定期检查大小。

实际验收需手动重启手机、解锁，确认不打开 Termux 的情况下 SSH 和公网博客恢复。手动执行通过不等于已验证 Android 开机广播。

如需停用，只把 `10-zuoer-server` 移出 boot 目录；不会停止已运行服务。无需持续保活时可手动执行 `termux-wake-unlock`。
