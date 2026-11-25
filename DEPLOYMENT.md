# Thông Tin Triển Khai (Deployment Information)

## Trạng thái

Mã nguồn agent Part 6 (`06-lab-complete/`) và cấu hình nền tảng (`render.yaml`, `railway.toml`) đã hoàn thiện. Dịch vụ **chưa được deploy lên cloud** nên chưa có URL công khai hoặc ảnh chụp màn hình triển khai.

## URL Công Khai (Public URL)

*(Điền sau khi deploy lên Render hoặc Railway, ví dụ: `https://day14-production-agent.onrender.com`)*

## Nền tảng triển khai

- **Khuyến nghị chính:** Render (sử dụng Blueprint trong `06-lab-complete/render.yaml`, đã khai báo sẵn web service Docker cho `06-lab-complete` và dịch vụ Redis Key Value miễn phí).
- **Dự phòng / đối chiếu rubric:** Railway (`06-lab-complete/railway.toml`). Lưu ý Railway xem `railway.toml` là định dạng Config as Code cũ (ngừng đọc từ 2026-12-01), nên nếu deploy mới lên Railway cần cấu hình qua Dashboard hoặc Railway IaC và tạo thêm dịch vụ Redis rồi gán `REDIS_URL`.

## Biến môi trường đã cấu hình trên nền tảng

Không commit giá trị bí mật vào mã nguồn hay Git. Các biến đặt trên dashboard nền tảng:

- `PORT` (nền tảng tự cấp, app tự đọc từ biến môi trường)
- `ENVIRONMENT` (`production`)
- `AGENT_API_KEY` (giá trị ngẫu nhiên sinh tự động / secret trên dashboard)
- `REDIS_URL` (chuỗi kết nối tới Redis trên nền tảng)
- `RATE_LIMIT_PER_MINUTE` (`10`)
- `DAILY_BUDGET_USD` (`1.0`)

## Lệnh kiểm tra sau khi deploy (4 lệnh tự kiểm CP6)

Sau khi deploy, đặt `BASE` là URL công khai và `AGENT_API_KEY` là khóa đã cấu hình trên nền tảng rồi chạy:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/health"                                                          # Kỳ vọng: 200
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/ready"                                                           # Kỳ vọng: 200
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -d '{"question":"Hello"}'   # Kỳ vọng: 401
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -H "X-API-Key: $AGENT_API_KEY" -d '{"question":"Hello"}'   # Kỳ vọng: 200
```

Kiểm tra thêm bằng script chấm:

```bash
cd 06-lab-complete
python check_production_ready.py --public-url "$BASE"
```

## Ảnh chụp màn hình (Screenshots)

*(Cần bổ sung sau khi deploy lên cloud)*

- [Bảng điều khiển triển khai (Dashboard)](screenshots/dashboard.png) — chưa chụp
- [Dịch vụ đang chạy (Service running)](screenshots/running.png) — chưa chụp
- [Kết quả kiểm thử 4 lệnh curl](screenshots/test.png) — chưa chụp
