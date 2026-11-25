# Benchmark & Observability Report — Day 14

> Mọi số liệu hiệu năng, chất lượng, trace và alert trong báo cáo đều lấy trực tiếp từ các file JSON trong `reports/`, file CSV trong `benchmark-results/` và các ảnh chụp thật trong `screenshots/`.

**Họ tên:** Hồ Đức Mạnh — MSSV: 2A202603609 (Lớp K5-L3A)  
**Ngày chạy:** 2026-11-25  
**Môi trường:** Fedora 44 Linux (x86_64), Podman 5.8.4 + Docker Compose v2.33.1, Python 3.14 (host) / Python 3.11-slim (container). Các file JSON CP7 local chạy với `MOCK_ERROR_RATE=0` để cô lập latency; phần CP8 chạy full Docker Compose stack (`agent`, `nginx`, `prometheus`, `grafana`, `jaeger`, `locust`).

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

- [x] Dashboard Grafana khi đang có tải (thấy rõ Golden Signals: Traffic `61.9 req/s`, Error rate `1.15%`, Latency p95 `293.22 ms`, Saturation `14`, Instances up `3`, LLM cost 1h `$0.4479`, Retrieval hit ratio `100%`, và phân tải đều trên 3 instance): [screenshots/grafana-dashboard.png](screenshots/grafana-dashboard.png)
- [x] Một trace chậm trong Jaeger (`aad63da43740e3411d5e5c8c304855dd`, tổng `2.1s`, span `chat mock-llm-small` chiếm `1.7s`): [screenshots/jaeger-slow-trace.png](screenshots/jaeger-slow-trace.png)
- [x] Một trace lỗi trong Jaeger (`c479712c2cf8f1fc922bd868cceba04f`, HTTP `503`, `error.type = upstream_unavailable`, kèm event `exception`): [screenshots/jaeger-error-trace.png](screenshots/jaeger-error-trace.png)
- [x] Trang Alerts của Prometheus với cả 4 alert đang **firing** cùng lúc (`LLMCostBurnRateHigh` = `$17.84/giờ`, `AgentHighErrorRate` = `20.14%`, `AgentHighLatencyP95` = `1.95s`, `AgentInstanceDown` = `0`): [screenshots/prometheus-alert-firing.png](screenshots/prometheus-alert-firing.png)

**Trả lời câu hỏi Exercise 7.4 (quan sát từ dashboard Grafana & cấu hình stack):**
- **Khoảng cách giữa avg và p95/p99:** Trên biểu đồ *Latency /ask*, `avg` và `p50` nằm quanh ~190–230 ms trong khi `p99` nhảy lên ~1,8 s. Nguyên nhân là mock LLM có `MOCK_SLOW_RATE=0.03` (~3% request bị cộng thêm `MOCK_SLOW_MS=1500ms`); giá trị trung bình bị kéo xuống bởi ~97% request nhanh nên che giấu nhóm người dùng chịu tail latency.
- **Vì sao input tokens > output tokens:** Trên panel *Tokens/s*, input token (~5K tok/s) luôn cao hơn output token (~2,5K tok/s) vì agent v2 ghép `SYSTEM_PROMPT` + đoạn tài liệu retrieve từ knowledge base (`context`) + câu hỏi vào prompt đầu vào, dài hơn nhiều so với câu trả lời ngắn gọn sinh ra.
- **Vì sao `/metrics` bị chặn ở Nginx (`GET /metrics` → HTTP `404`):** Endpoint `/metrics` tiết lộ thông tin vận hành nội bộ (lưu lượng, route, tỷ lệ lỗi, chi phí LLM, số instance). Nginx chặn truy cập công khai từ bên ngoài để đảm bảo bảo mật và tránh bị scrape trái phép; chỉ Prometheus trong mạng nội bộ Docker (`obs_net`) được scrape trực tiếp container `agent:8000/metrics`.

### 4.2 Thí nghiệm "phá hệ thống"

Kiểm tra unit test cho alert rules (`promtool test rules /p/alert_rules_test.yml`): **`SUCCESS`**.

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | `AgentHighErrorRate` (`for: 1m`, giá trị đo: **20.14%**) | **75 giây** (sau khi áp dụng + tải Locust) | *Error rate* (Golden Signals), *Requests/s theo status code* (`503`), *LLM calls theo kết quả* |
| B | `MOCK_SLOW_RATE=0.3` | `AgentHighLatencyP95` (`for: 2m`, giá trị đo: **1.95 s**) | **135 giây** (sau khi áp dụng + tải Locust) | *Latency p95*, *Latency /ask — p50 / p95 / p99* |
| C | `LLM_MODEL=mock-llm-large` | `LLMCostBurnRateHigh` (`for: 2m`, giá trị đo: **$17.84/giờ**) | **~120 giây** (burn rate vượt `$2/giờ`; đã firing từ lúc chạy benchmark tải cao và tăng gấp ~16× lên `$17.84/giờ` khi chuyển sang `mock-llm-large`) | *Cost burn rate (USD/giờ)*, *LLM cost (1h)*, *LLM latency p95 theo model* |
| D | `docker pause` 1 instance (`agent-2`) | `AgentInstanceDown` (`for: 30s`, `up == 0`) | **40 giây** (từ lúc `docker pause` đến lúc `firing`) | *Instances up* (giảm từ 2 xuống 1), *Requests/s theo instance* |
| E | `AGENT_VERSION=v1` | **Không có alert nào firing** | Không firing | *Retrieval hit ratio (agent v2)* (mất/về 0%), *Tokens/s* (giảm), bảng *version* đổi sang `v1` (`agent_info{version="v1"} = 1`) |

**Phân tích thí nghiệm D & E:**
- **Vì sao thí nghiệm D dùng `docker pause` thay vì `docker stop`, và vì sao lỗi 504 không hiện trên metric của agent:** Prometheus phát hiện agent qua Docker DNS (`dns_sd_configs`). Khi `docker stop`, container biến mất khỏi DNS nên Prometheus bỏ target thay vì báo `up == 0`; còn khi `docker pause`, container vẫn có trong DNS nhưng bị treo nên scrape fail → `up == 0` và `AgentInstanceDown` firing sau 40 giây. Các lỗi `504 Gateway Timeout` do Nginx chờ quá `proxy_read_timeout` xảy ra ở tầng load balancer khi agent không xử lý xong request, nên counter của chính service agent không đếm được — production cần giám sát thêm ở tầng Nginx/LB hoặc synthetic probe từ bên ngoài.
- **Thí nghiệm E không làm alert nào firing — cách phát hiện trong production:** Hạ tầng vẫn xanh (latency thậm chí nhanh hơn, error rate không đổi, chi phí giảm) dù chất lượng câu trả lời tụt mạnh (từ 100% xuống ~4,3%). Cần phát hiện bằng **eval quality gate trên golden dataset trong CI/CD trước khi deploy** (chặn merge/release khi accuracy giảm hoặc có regression), kết hợp **đánh giá chất lượng định kỳ trên traffic mẫu (online eval / LLM-as-judge)** và theo dõi chỉ số nghiệp vụ/RAG (như `retrieval_hit_ratio`, phản hồi thumbs-down của người dùng).

### 4.3 Debug bằng trace

**Trace chậm nhất tìm được trong Jaeger:**

- `trace_id`: `aad63da43740e3411d5e5c8c304855dd`
- Tổng thời gian (`POST /ask`): **2122.8 ms** (~2.1 s)
- Phân rã span:
  - `agent.run`: ~1.8 s
  - `agent.retrieve_context`: **74.8 ms** (~3,5%)
  - Span chiếm nhiều thời gian nhất: **`chat mock-llm-small`** — **~1.7 s (~1700 ms, chiếm ~80,1% tổng thời gian)** (Input: 81 tokens, Output: 46 tokens) → chứng minh nút thắt nằm ở lời gọi LLM upstream (tail latency), không phải bước retrieval hay code FastAPI.
- Dòng log JSON tương ứng (lấy trực tiếp từ `docker compose -p k5-day14-observability logs agent` theo `trace_id`):

```json
{"ts": "2026-11-25T11:12:21.534403+00:00", "level": "INFO", "service": "observable-agent", "instance": "c00899899b02", "event": "http_request", "trace_id": "aad63da43740e3411d5e5c8c304855dd", "span_id": "19ee7463352f9e34", "request_id": "ec9f0387e142", "method": "POST", "route": "/ask", "status": 200, "ms": 2122.8}
```

**Trace lỗi tìm được trong Jaeger:**

- `trace_id`: `c479712c2cf8f1fc922bd868cceba04f` (HTTP `503`, tổng `110 ms`, span `chat mock-llm-small` `84.3 ms` có `error.type = upstream_unavailable` và event `exception`):

```json
{"ts": "2026-11-25T11:14:15.587578+00:00", "level": "INFO", "service": "observable-agent", "instance": "24220f74977b", "event": "llm_error", "trace_id": "c479712c2cf8f1fc922bd868cceba04f", "span_id": "a1d553cdcd8468ba", "request_id": "0df498f325ff", "error": "Upstream LLM error: 503 Service Unavailable (mock)"}
```

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

Số liệu đối chiếu trực tiếp với [benchmark-results/scale_1_stats.csv](benchmark-results/scale_1_stats.csv) và [benchmark-results/scale_3_stats.csv](benchmark-results/scale_3_stats.csv):

**Endpoint `POST /ask`:**

| Số instance | Tổng req | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7.078 | 59.41 | 190 | 390 | 1700 | 67 (0,95%) |
| 3 | 7.195 | 60.41 | 190 | 220 | 1700 | 78 (1,08%) |

**Tổng hợp (`Aggregated` — gồm `POST /ask` và `GET /health`):**

| Số instance | Tổng req | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7.818 | 65.62 | 190 | 330 | 1700 | 67 (0,86%) |
| 3 | 7.876 | 66.12 | 190 | 220 | 1700 | 78 (0,99%) |

**Giải thích kết quả:**
- Khi tăng từ **1 → 3 instance**, **p95 của `POST /ask` giảm rõ rệt từ 390 ms xuống 220 ms** (giảm ~43,6%; và trên `GET /health`, p95 giảm từ 18 ms xuống 8 ms, max từ 625 ms xuống 51 ms) vì tải CPU/event-loop không còn bị dồn vào 1 container giới hạn `0.5 CPU`.
- Tuy nhiên, **RPS chỉ tăng nhẹ (~59,4 → ~60,4 req/s)** và **p50 (190 ms) cùng p99 (1700 ms) gần như không đổi**. Nút thắt không còn nằm ở CPU của FastAPI mà nằm ở **độ trễ I/O từ LLM upstream** (`MOCK_LATENCY_MS` + `MOCK_SLOW_MS=1500ms` chiếm >80% thời gian request, cùng với `wait_time` giữa các request của 100 user Locust). Để giảm p99 thực sự, cần tối ưu phía LLM (streaming, semantic cache, timeout/retry hoặc fallback model), không chỉ scale ngang số container agent.

## 6. Kết luận

- 3 điều rút ra từ các phép đo local:
  1. Concurrency giúp tăng throughput tới một điểm; ở concurrency 100, host bị bão hoà và p95/p99 vượt SLO rõ rệt.
  2. p99 nhạy với slow requests ở mức 3%; khi tỉ lệ chậm vượt 5%, p95 cũng phản ánh vấn đề.
  3. Retrieval cải thiện mạnh accuracy; cost/câu đúng là chỉ số so sánh hữu ích hơn cost/câu khi số câu trả lời đúng khác nhau.
- Nếu đưa agent lên production thật, cần theo dõi thêm budget theo user/model, Redis availability/latency, queue depth, cache hit rate và chất lượng theo nhóm câu hỏi.

**CI quality gate:** chạy `run_eval.py` với `--min-accuracy 1.0` và `--baseline reports/eval_v2.json`; exit code 1 sẽ fail job và chặn merge.
