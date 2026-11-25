# Thông Tin Triển Khai (Deployment Information)

## URL Công Khai (Public URL)

https://day14-production-agent-u3t1.onrender.com

## Nền tảng triển khai

- **Nền tảng chính:** **Render** (region `singapore`, gói `free`)
- **Web Service:** `day14-production-agent` (runtime `docker`, `rootDir: 06-lab-complete`, `healthCheckPath: /health`, đọc cấu hình từ `06-lab-complete/Dockerfile` và `06-lab-complete/render.yaml`)
- **Redis / Key Value:** `day14-agent-redis` (Render Key Value, gói `free`, region `singapore`, kết nối nội bộ qua `REDIS_URL`)

## Biến môi trường đã cấu hình trên Render

Tất cả biến cấu hình và khóa bí mật được thiết lập trực tiếp trên Render Dashboard (không commit vào mã nguồn hay lịch sử Git):

- `PORT` *(Render tự cấp, container đọc qua `${PORT:-8000}`)*
- `ENVIRONMENT` (`production`)
- `AGENT_API_KEY` *(khóa bí mật ngẫu nhiên đặt trong Environment của Render, không lưu trong repo)*
- `REDIS_URL` *(chuỗi kết nối nội bộ tới dịch vụ `day14-agent-redis`)*
- `RATE_LIMIT_PER_MINUTE` (`10`)
- `DAILY_BUDGET_USD` (`1.0`)

## Lệnh kiểm tra và kết quả thực tế (4 lệnh tự kiểm CP6)

Đặt `BASE="https://day14-production-agent-u3t1.onrender.com"` và `AGENT_API_KEY` theo giá trị trên Render Dashboard:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/health"                                                          # 200
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/ready"                                                           # 200
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -d '{"question":"Hello"}'   # 401
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -H "X-API-Key: $AGENT_API_KEY" -d '{"question":"Hello"}'   # 200
```

Kết quả đo thực tế trên URL công khai:

```text
GET  /health              -> 200  {"status":"ok"}
GET  /ready               -> 200  {"ready":true}
POST /ask (không có key)  -> 401  {"detail":"Invalid or missing X-API-Key"}
POST /ask (có X-API-Key)  -> 200  {"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"input_tokens":2,"output_tokens":17,"cost_usd":1.05e-05}}
```

## Ảnh chụp màn hình (Screenshots)

- [Dịch vụ đang chạy trên Render — Swagger UI `/docs`](screenshots/running.png) ✅
- [Bảng điều khiển triển khai trên Render Dashboard](screenshots/dashboard.png) *(bổ sung từ trình duyệt Render Dashboard đã đăng nhập tại https://dashboard.render.com/web/srv-dc3bm9navr4c73euf4h0)*
- [Kết quả kiểm thử 4 lệnh curl CP6 (`200 / 200 / 401 / 200`)](screenshots/test.png) *(chụp terminal chạy 4 lệnh trên, nhớ che `AGENT_API_KEY`)*
