# 部署

## MediaMTX

从官方项目获取适合架构的版本。本次实机使用 1.21.2，其他版本的 API 和配置字段可能不同。参考 `config/mediamtx.example.yml`，另存本地配置，填写真实源地址；配置文件含密码，限制其读取权限。

确保原始流能解码后启动 FFmpeg：

```sh
ffmpeg -hide_banner -loglevel warning -nostdin \
  -rtsp_transport tcp -timeout 15000000 \
  -i rtsp://127.0.0.1:8554/joaan/main \
  -map 0:v:0 -an -vf scale=1920:1080 -r 15 \
  -c:v libx264 -preset veryfast -tune zerolatency \
  -profile:v main -level:v 4.0 -pix_fmt yuv420p \
  -b:v 2048k -maxrate 2048k -bufsize 4096k -g 30 -bf 0 \
  -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/joaan/nvr
```

输出只有视频。转码消耗 CPU，每新增一路需要评估性能；不能把单路成功外推为无限多路。

## ONVIF 最小代理

```sh
PUBLIC_HOST=192.168.10.10 ONVIF_BIND=192.168.10.10 \
ALLOWED_NETWORKS=127.0.0.0/8,192.168.10.0/24,192.168.20.0/24 \
python3 src/onvif_relay.py
```

NVR 手动添加服务器 IP、ONVIF 端口 8899。该代理单 profile、只读、无用户认证，不应扩大到不可信来源网段。输出 URI 固定指向 `joaan/nvr`；其声明的编码参数必须与 FFmpeg 实际输出保持一致。

## Web 管理服务

参考 README 初始化 `auth.json`。使用独立运行用户，确保 DATA_DIR 可写，auth.json/cameras.json 不可被其他普通用户读取；应用代码和 Web 文件只读。Web 默认监听本机。生产环境应由有经验的管理员增加 HTTPS、可信来源限制和网络隔离。

参考 `deploy/dashboard.service` 设置 PUBLIC_HOST、WEB_BIND、代码目录。服务以专用账户运行前先建立用户和数据目录，并用该账户初始化管理密码。此模板不会替你安装 MediaMTX 或改变路由器配置。

新增设备通过 MediaMTX localhost API 创建 `cams/<id>/main` 和可选 `sub`。`cameras.json` 保存恢复用配置，后台循环重建缺失路径。不要同时用其他工具修改同名路径。已有路径的外部修改不会被强制覆盖。操作失败时应检查 MediaMTX 的实际配置，原型尚无事务回滚。

## 重启验收

依次验证摄像头重启、管理服务重启、中转进程重启、服务器重启。确认地址不变、原始流恢复、转码恢复、NVR 出图与录像回放。仓库自带测试仅覆盖无设备的协议逻辑，不能替代你现场的长时间验收。
