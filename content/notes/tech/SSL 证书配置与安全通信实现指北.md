+++
title = "SSL 证书配置与安全通信实现指北"
author = "CC"
date = 2026-04-14T00:00:00
tags = ["SSL/TLS"]
categories = ["note"]
draft = false
toc = true
+++

<!--
> [!tip] notes
> 一篇笔记包含出本释义、使用示例、参考文献、个人感受和评价等。
-->

事情是这样的，我在写前端页面用到 `DeviceMotionEvent` 的时候，发现它总是在报错, 提示 "DeviceMotionEvent is not available"。查了下发现，在现代浏览器中，访问敏感 API 必须在**安全上下文**（HTTPS/WSS）中才行，目的是保护保护数据不被窃取或篡改。比如

- `DeviceMotionEvent`（提供设备的位置和方向的改变速度的信息）
- `DeviceOrientationEvent`（提供设备方向的信息）
- 摄像头和麦克风 API
- Web Bluetooth API
- Web USB API

因此我需要给 http/ws 服务增加 SSL/TLS 加密，升级为 https/wss 服务。

## 概念梳理

`SSL` (Secure Sockets Layer) 一种网络安全协议，用于对客户端和服务器端之间的身份认证，加密传输数据，确保传输数据的保密性、完整性，实现两者之间的安全通信。

`TLS` (Transport Layer Security) 传输层安全协议，由于SSL协议存在安全隐患，互联网工程任务组IETF于1999年推出了TLS，它提供更强的加密算法和改进的验证方法，被视为SSL的继任者，是SSL的更新、更安全版本。

`SSL/TLS`最常见的应用是SSL/TLS证书（也称为`SSL证书`），网站部署`SSL证书`实现`HTTPS`协议的加密，确保对浏览器和网站服务器之间的所有传输数据的完整性和保密性，可有效防止中间人攻击的拦截和篡改数据。

`HTTPS` (Hypertext Transfer Protocol Secure) 超文本传输安全协议，是全球网络安全通信的标准协议。HTTPS是HTTP的安全版本，它基于HTTP进行通信，通过利用`SSL/TLS`等协议来实现数据加密传输、完整性保护和身份可信验证，防止传输数据被泄露或篡改，确保客户端与服务器端的网络通信安全。

## 生成 SSL 证书和密钥对

### 使用 OpenSSL 命令行工具

```bash
# 生成私钥
openssl genrsa -out key.pem 2048

# 生成自签名证书
openssl req -new -x509 -key key.pem -out cert.pem -days 365 -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
```

- 证书 = 公钥 + 申请者与颁发者信息 + 签名
- 证书的后缀不能作为证书编码的依据。

### 使用 Python cryptography 库

```python
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import ipaddress

# 生成私钥
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# 创建证书
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
    x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    private_key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.utcnow()
).not_valid_after(
    # 证书有效期一年
    datetime.utcnow() + timedelta(days=365)
).add_extension(
    x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]),
    critical=False,
).sign(private_key, hashes.SHA256())

# 保存证书和私钥
with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

with open("key.pem", "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))
```

### 3. 项目中的证书生成实现

在 `touchpad/network/http.py` 中，实现了自动证书生成：

```python
def _generate_self_signed_cert(self) -> tuple:
    """生成自签名证书"""
    import os
    import tempfile
    from datetime import datetime, timedelta
    
    # 创建临时证书文件
    cert_fd, cert_path = tempfile.mkstemp(suffix='.pem')
    key_fd, key_path = tempfile.mkstemp(suffix='.key')
    
    # 关闭文件描述符，让ssl模块可以使用这些文件
    os.close(cert_fd)
    os.close(key_fd)
    
    # 使用 OpenSSL 生成自签名证书（如果系统中有 OpenSSL）
    try:
        import subprocess
        # 生成私钥
        subprocess.run([
            'openssl', 'genrsa', '-out', key_path, '2048'
        ], check=True, capture_output=True)
        
        # 生成自签名证书
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-key', key_path, 
            '-out', cert_path, '-days', '365', '-subj', 
            f'/C=CN/ST=State/L=City/O=Organization/CN={self._host}'
        ], check=True, capture_output=True)
        
        logger.info(f"自签名证书已生成: {cert_path}, {key_path}")
        return cert_path, key_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 如果没有 OpenSSL，回退到使用 cryptography 库生成证书
        logger.warning("OpenSSL 未找到，将尝试使用 Python cryptography 库生成证书")
        
        # 删除之前创建的临时文件
        os.unlink(cert_path)
        os.unlink(key_path)
        
        try:
            # 尝试使用 cryptography 库生成证书
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            
            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # 创建证书
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
                x509.NameAttribute(NameOID.COMMON_NAME, self._host),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).sign(private_key, hashes.SHA256())
            
            # 写入证书文件
            cert_path = os.path.join(tempfile.gettempdir(), f"temp_cert_{os.getpid()}.pem")
            key_path = os.path.join(tempfile.gettempdir(), f"temp_key_{os.getpid()}.key")
            
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            logger.info(f"使用 cryptography 库生成的证书: {cert_path}, {key_path}")
            return cert_path, key_path
        
        except ImportError:
            # 如果没有 cryptography 库，回退到创建占位符文件
            logger.warning("cryptography 库未安装，将创建临时证书文件")
            
            cert_path = os.path.join(tempfile.gettempdir(), f"temp_cert_{os.getpid()}.pem")
            key_path = os.path.join(tempfile.gettempdir(), f"temp_key_{os.getpid()}.key")
            
            # 创建占位符证书文件（实际部署时应替换为真实证书）
            with open(cert_path, 'w') as cert_file:
                cert_file.write("-----BEGIN CERTIFICATE-----\n")
                cert_file.write("# 临时证书，实际部署时应替换为真实证书\n")
                cert_file.write("-----END CERTIFICATE-----\n")
            
            with open(key_path, 'w') as key_file:
                key_file.write("-----BEGIN PRIVATE KEY-----\n")
                key_file.write("# 临时私钥，实际部署时应替换为真实私钥\n")
                key_file.write("-----END PRIVATE KEY-----\n")
            
            logger.info(f"临时证书已创建: {cert_path}, {key_path}")
            return cert_path, key_path
```

## 在项目中启用 SSL 加密

### HTTPServer 开启 SSL 加密

```python
import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("path/to/cert_file", "path/to/key_file")

httpd = HTTPServer(("localhost", 8000), SimpleHTTPRequestHandler)
# Wrap socket with SSL
httpd.socket = ssl_context.wrap_socket(
   httpd.socket,
   server_side=True,
)

httpd.serve_forever()
```

### websocket 开启 SSL 加密

```python
# WSS (WS over TLS) server example, with a self-signed certificate

import asyncio
import pathlib
import ssl
import websockets

async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"

    await websocket.send(greeting)
    print(f"> {greeting}")

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
ssl_context.load_cert_chain(localhost_pem)

start_server = websockets.serve(
    hello, "localhost", 8765, ssl=ssl_context
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


# WSS (WS over TLS) client example, with a self-signed certificate

import asyncio
import pathlib
import ssl
import websockets

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
localhost_pem = pathlib.Path(__file__).with_name("localhost.pem")
ssl_context.load_verify_locations(localhost_pem)

async def hello():
    uri = "wss://localhost:8765"
    async with websockets.connect(
        uri, ssl=ssl_context
    ) as websocket:
        name = input("What's your name? ")

        await websocket.send(name)
        print(f"> {name}")

        greeting = await websocket.recv()
        print(f"< {greeting}")

asyncio.get_event_loop().run_until_complete(hello())
```

官方文档：[websocket](https://websockets.readthedocs.io/en/9.1/intro.html)

### 前端适配

当启用 SSL 后，前端页面会自动使用安全协议，根据协议类型选择 websocket 连接方式：

```javascript
// 根据页面协议自动选择连接方式
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const ws = new WebSocket(protocol + window.location.hostname + ':' + WEBSOCKET_PORT);
```

## 生产环境实践

### 证书管理

- 使用由受信任的 CA 签发的正式证书
- 实施证书自动续期机制（如 Let's Encrypt + Certbot）
- 定期更换证书（建议每年更换一次）

### 基于 Nginx 配置 SSL 加密代理

在生产环境中，推荐使用 Nginx 作为反向代理：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # WebSocket 支持
    location / {
        proxy_pass http://localhost:9876;  # HTTP 服务器端口
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# WebSocket 专用配置
server {
    listen 443 ssl http2;
    server_name ws.your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:9877;  # WebSocket 服务器端口
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 安全注意事项

- 不要在版本控制系统中存储私钥
- 实施适当的访问控制
- 定期审查 SSL 配置
- 监控证书过期时间
- 使用 HSTS (HTTP Strict Transport Security) 增强安全性

## 小结

| 环境 | 证书类型    | 配置     | 注意事项             |
| ---- | ----------- | -------- | -------------------- |
| 开发 | 自签名证书  | 宽松验证 | 浏览器会显示安全警告 |
| 生产 | CA 签发证书 | 严格验证 | 用户无安全警告       |

通常，在生产环境下，使用 CA 签发的正式证书，通过 Nginx 配置 SSL 加密代理，不需要在业务代码层面进行特殊处理。
但涉及到前端敏感 API 则必须配置 ssl 认证的开发环境，这时候可以使用自签名证书进行测试。
