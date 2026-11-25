# Benchmark & Observability Report — Day 14

> Các số liệu hiệu năng/chất lượng trong báo cáo lấy từ JSON trong `reports/`. Những phần cần Docker không được ước lượng; môi trường chạy không có Docker CLI/daemon.

**Họ tên:** Hồ Đức Mạnh — MSSV: 2A202603609 (Lớp K5-L3A)  
**Ngày chạy:** 2026-11-25  
**Môi trường:** Linux (x86_64). Các file JSON CP7 hiện có được đo trước đó trong môi trường không có Docker (CPython 3.9.13); phần CP8 (Docker stack) cần chạy trên host Linux có Docker Engine để bổ sung số liệu CSV, trace và ảnh chụp thật.

Các lần đo local đặt `MOCK_ERROR_RATE=0` để cô lập latency; load test concurrency và ba mẫu slow-rate dùng `MOCK_SLOW_RATE` lần lượt là mặc định 0.03 và 0 / 0.03 / 0.1.

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | ≤ 500 ms | Phù hợp ngưỡng của script lab; p95 thể hiện phần lớn request và không bị che bởi average. |
| Error rate `/ask` | ≤ 2% | Ngưỡng của script lab; tương ứng error budget 2%. |
| Accuracy trên golden dataset | ≥ 100% sau khi sửa v2 | Lab yêu cầu v2 đạt 23/23 và không regression trước quality gate cuối. |

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2; 300 requests mỗi mức)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO p95 / error |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 4.45 | 190.5 | 219.2 | 1685.9 | 0.00% | PASS |
| 10 | 37.30 | 187.1 | 218.5 | 1696.2 | 0.00% | PASS |
| 50 | 103.65 | 195.9 | 248.0 | 1700.2 | 0.00% | PASS |
| 100 | 45.02 | 475.6 | 4326.8 | 4736.5 | 0.00% | FAIL — p95 |

**Nhận xét:** RPS tăng từ concurrency 1 đến 50 nhưng giảm ở 100; không tăng tuyến tính. Ở mức 100, p95 tăng lên 4.33 s và p99 lên 4.74 s. Đây là điểm nghẽn của execution sandbox/máy chạy khi tải đồng thời cao; cần đo lại trên host lab có cấu hình xác định trước khi kết luận về production.

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---:|---:|---:|---:|
| 0 | 192.7 | 225.5 | 243.9 |
| 0.03 (mặc định) | 246.3 | 225.9 | 1714.0 |
| 0.1 | 314.4 | 1686.6 | 1714.0 |

**Nhận xét:** Khi tỉ lệ slow là 3%, p99 nhảy mạnh trong khi p95 gần như không đổi. Khi slow rate lên 10%, p95 cũng tăng vì số request chậm vượt 5% mẫu. Average không thể chỉ ra rõ ai bị tail latency và có thể che mất trải nghiệm xấu ở phần đuôi.

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 ban đầu | Agent v2 sau sửa KB |
|---|---:|---:|---:|
| Accuracy | 4.3% (1/23) | 91.3% (21/23) | 100% (23/23) |
| Avg tokens / câu | 56.4 | 108.8 | 114.9 |
| Tổng cost (USD) | 0.000395 | 0.000757 | 0.000801 |
| Cost / câu đúng (USD) | 0.00039495 | 0.00003607 | 0.00003485 |
| Quality gate | FAIL | PASS (≥80%, không regression) | PASS (≥100%, không regression) |

**Những câu v2 trả lời sai ban đầu và cách sửa:**

| ID | Keyword bị thiếu | Sửa trong knowledge base |
|---|---|---|
| `security-02` | `token`, `hết hạn`, `chữ ký` | Thêm mô tả JWT là token có chữ ký và expiry, so sánh với API key tĩnh. |
| `scaling-03` | `cpu`, `memory`, `custom metrics` | Thêm tài liệu Kubernetes HPA scale theo CPU/memory và custom metrics. |

**Trade-off:** v2 tăng accuracy từ 4.3% lên 91.3% ban đầu, rồi 100% sau khi bổ sung hai tài liệu. Đổi lại, v2 dùng nhiều token hơn và latency p95 cao hơn một chút; cost trên mỗi câu đúng giảm từ 0.00039495 USD ở v1 xuống 0.00003485 USD ở v2 đã sửa.

## 4. Observability stack (production)

### 4.1 Screenshot

- [ ] Grafana dashboard khi có tải — chưa chạy; Docker không có trong môi trường.
- [ ] Trace chậm trong Jaeger — chưa chạy; Docker không có trong môi trường.
- [ ] Trace lỗi trong Jaeger — chưa chạy; Docker không có trong môi trường.
- [ ] Prometheus Alerts với ít nhất 2 alert firing — chưa chạy; Docker không có trong môi trường.

Ảnh Part 3/6 (`dashboard.png`, `running.png`, `test.png`) và Part 7 (`grafana-dashboard.png`, `jaeger-slow-trace.png`, `jaeger-error-trace.png`, `prometheus-alert-firing.png`) hiện chưa có.

**Trả lời câu hỏi Exercise 7.4 (phân tích kiến trúc & cấu hình stack):**
- **Khoảng cách giữa avg và p95/p99:** Vì mock LLM mô phỏng ~3% request chậm bất thường (`MOCK_SLOW_RATE=0.03`, cộng thêm `MOCK_SLOW_MS=1500ms`), độ trễ trung bình (`avg`) bị kéo xuống bởi ~97% request nhanh nên trông vẫn thấp, trong khi `p95`/`p99` phản ánh trực tiếp nhóm request bị tail latency.
- **Vì sao input tokens > output tokens:** Ở agent v2, prompt gửi vào LLM ghép `SYSTEM_PROMPT` + đoạn tài liệu tìm được từ knowledge base (`context`) + câu hỏi của người dùng, nên tổng lượng token đầu vào luôn lớn hơn câu trả lời ngắn gọn ở đầu ra.
- **Vì sao `/metrics` bị chặn ở Nginx (`return 404`):** Endpoint `/metrics` tiết lộ thông tin vận hành nội bộ (lưu lượng, tên route, tỷ lệ lỗi, model/chi phí, số instance). Nginx chặn truy cập công khai từ bên ngoài để tránh lộ thông tin và tránh bị lạm dụng scrape gây tốn tài nguyên; chỉ Prometheus trong mạng Docker nội bộ được scrape trực tiếp container `agent:8000/metrics`.

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | Chưa chạy | Chưa đo | Chưa đo |
| B | `MOCK_SLOW_RATE=0.3` | Chưa chạy | Chưa đo | Chưa đo |
| C | `LLM_MODEL=mock-llm-large` | Chưa chạy | Chưa đo | Chưa đo |
| D | `docker pause` 1 instance | Chưa chạy | Chưa đo | Chưa đo |
| E | `AGENT_VERSION=v1` | Chưa chạy | Chưa đo | Chưa đo |

Docker stack không thể khởi chạy trong môi trường này nên không có thời gian alert hay ảnh thật để ghi. Thay đổi `AGENT_VERSION=v1` làm giảm chất lượng mà metric latency/error không nhất thiết đổi; phát hiện bằng eval quality gate trên golden dataset trong CI trước deploy.

### 4.3 Debug bằng trace

Chưa có trace ID/span/log thực tế: Jaeger stack không chạy được khi thiếu Docker. Không tự tạo trace giả.

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---:|---:|---:|---:|---:|---:|
| 1 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| 3 | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |

CSV `scale_1_stats.csv` và `scale_3_stats.csv` chưa được tạo vì lệnh Locust chạy qua Docker Compose. Cần chạy CP8 trên host có Docker, chép CSV vào `benchmark-results/`, rồi cập nhật báo cáo theo số thật.

## 6. Kết luận

- 3 điều rút ra từ các phép đo local:
  1. Concurrency giúp tăng throughput tới một điểm; ở concurrency 100, host bị bão hoà và p95/p99 vượt SLO rõ rệt.
  2. p99 nhạy với slow requests ở mức 3%; khi tỉ lệ chậm vượt 5%, p95 cũng phản ánh vấn đề.
  3. Retrieval cải thiện mạnh accuracy; cost/câu đúng là chỉ số so sánh hữu ích hơn cost/câu khi số câu trả lời đúng khác nhau.
- Nếu đưa agent lên production thật, cần theo dõi thêm budget theo user/model, Redis availability/latency, queue depth, cache hit rate và chất lượng theo nhóm câu hỏi.

**CI quality gate:** chạy `run_eval.py` với `--min-accuracy 1.0` và `--baseline reports/eval_v2.json`; exit code 1 sẽ fail job và chặn merge.
