# k6 Load Testing Suite

This directory contains k6 load testing scripts for the Amazcope API.

## Prerequisites

### Install k6

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Docker:**
```bash
docker pull grafana/k6:latest
```

### Create Test Users

Before running load tests, create test users in your database:

```bash
cd ../../backend/src

# Create 5 test users
for i in {1..5}; do
  uv run python -m users.commands create-user \
    --email "loadtest${i}@example.com" \
    --password "TestPass123!" \
    --is-active
done
```

## Test Scripts

### 1. throughput-test.js - SLI-007 Throughput Test

Tests API throughput with 500 concurrent virtual users.

**What it tests:**
- Successful requests per second under high load
- Multiple API endpoints (auth, products, metrics, notifications)
- Realistic usage patterns with randomized operations
- Response time degradation under load

**Usage:**

```bash
# Basic run
k6 run throughput-test.js

# Run with custom base URL
k6 run --env BASE_URL=https://api.amazcope.com throughput-test.js

# Export results to JSON
k6 run --out json=results/throughput-$(date +%Y%m%d-%H%M%S).json throughput-test.js

# Run with InfluxDB output (for Grafana visualization)
k6 run --out influxdb=http://localhost:8086/k6 throughput-test.js

# Run with cloud output (k6 Cloud)
k6 run --out cloud throughput-test.js

# Run with custom VU count (override default 500)
k6 run -u 1000 -d 5m throughput-test.js
```

**Expected Results:**

- **Total Requests**: >10,000 over test duration
- **Success Rate**: >95%
- **P95 Response Time**: <2,000ms
- **P99 Response Time**: <5,000ms
- **Error Rate**: <5%

### 2. spike-test.js - Spike Testing

Tests system behavior under sudden traffic spikes.

```bash
k6 run spike-test.js
```

### 3. soak-test.js - Endurance Testing

Tests system stability over extended periods (30+ minutes).

```bash
k6 run soak-test.js
```

### 4. ip-simulation-test.js - IP Simulation Testing

Tests API with requests appearing from different IP addresses. Useful for:
- Rate limiting validation (per-IP quotas)
- Geographic distribution testing
- IP-based security rules
- DDoS protection mechanisms

```bash
k6 run ip-simulation-test.js

# With InfluxDB for geographic metrics
k6 run --out influxdb=http://localhost:8086/k6 ip-simulation-test.js
```

**Features:**
- Simulates IPs from 4 regions (North America, Europe, Asia, Mobile)
- Weighted distribution (50% NA, 30% EU, 15% Asia, 5% Mobile)
- Tracks rate limit hits and unique IPs used
- Custom metrics per region

**See also:** `IP_SIMULATION_GUIDE.md` for detailed explanation

## Test Scenarios

### Steady Load (Default)
- **500 VUs** for 5 minutes
- Simulates sustained high traffic
- Tests: Authentication, Product CRUD, Metrics, Notifications

### Ramping Load
- Gradually increases from 0 → 500 VUs
- Stages: 0→100 (2m), 100→250 (2m), 250→500 (2m), 500 (5m sustained)
- Tests throughput degradation patterns

## Configuration

### Environment Variables

- `BASE_URL` - API base URL (default: `http://localhost:8000`)
- `VUS` - Number of virtual users (default: 500)
- `DURATION` - Test duration (default: 5m)

### Test Users

Edit `TEST_USERS` array in `throughput-test.js`:

```javascript
const TEST_USERS = new SharedArray('users', function () {
  return [
    { email: 'loadtest1@example.com', password: 'TestPass123!' },
    { email: 'loadtest2@example.com', password: 'TestPass123!' },
    // Add more users...
  ];
});
```

## Metrics & Thresholds

### Custom Metrics

- `successful_requests` - Success rate (%)
- `total_requests` - Total request count
- `auth_duration` - Authentication response time
- `product_list_duration` - Product listing response time
- `product_detail_duration` - Product detail response time
- `metrics_duration` - Metrics API response time
- `notifications_duration` - Notifications API response time

### Thresholds

```javascript
thresholds: {
  'total_requests': ['count>10000'],
  'successful_requests': ['rate>0.95'],
  'http_req_duration': ['p(95)<2000', 'p(99)<5000'],
  'http_req_failed': ['rate<0.05'],
}
```

## Results Analysis

### Terminal Output

k6 provides real-time metrics in the terminal:

```
✓ auth: status is 200
✓ products list: status is 200
✓ metrics: status is 200

checks.........................: 95.23% ✓ 9523      ✗ 477
data_received..................: 45 MB  150 kB/s
data_sent......................: 12 MB  40 kB/s
http_req_duration..............: avg=1.2s   min=100ms med=1s   max=5s   p(95)=2.5s p(99)=4s
http_reqs......................: 12000  40/s
successful_requests............: 95.23% ✓ 11428     ✗ 572
total_requests.................: 12000
```

### JSON Output

Export to JSON for custom analysis:

```bash
k6 run --out json=results.json throughput-test.js

# Analyze with jq
cat results.json | jq 'select(.type=="Point" and .metric=="http_req_duration") | .data.value' | jq -s 'add/length'
```

### Grafana Dashboard

1. **Setup InfluxDB:**
   ```bash
   docker run -d -p 8086:8086 influxdb:1.8
   ```

2. **Run test with InfluxDB output:**
   ```bash
   k6 run --out influxdb=http://localhost:8086/k6 throughput-test.js
   ```

3. **Import k6 dashboard in Grafana:**
   - Dashboard ID: 2587
   - URL: https://grafana.com/grafana/dashboards/2587

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Testing

on:
  schedule:
    - cron: '0 0 * * 0' # Weekly
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run throughput test
        run: |
          cd load-tests/k6
          k6 run --env BASE_URL=${{ secrets.API_URL }} throughput-test.js

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: load-tests/k6/results/
```

## Docker Usage

```bash
# Run test in Docker
docker run --rm -i grafana/k6:latest run - <throughput-test.js

# Run with environment variables
docker run --rm -i \
  -e BASE_URL=http://host.docker.internal:8000 \
  grafana/k6:latest run - <throughput-test.js

# Mount results directory
docker run --rm -i \
  -v $(pwd)/results:/results \
  grafana/k6:latest run \
  --out json=/results/output.json \
  - <throughput-test.js
```

## Troubleshooting

### Authentication Failures

If you see high auth failure rates:

1. **Check test users exist:**
   ```bash
   cd ../../backend/src
   uv run python -c "from users.models import User; from api.deps import get_async_db_context; import asyncio; async def check(): async with get_async_db_context() as db: from sqlalchemy import select; users = (await db.execute(select(User).where(User.email.like('loadtest%')))).scalars().all(); print(f'Found {len(users)} test users'); asyncio.run(check())"
   ```

2. **Verify credentials in script match database**

3. **Check JWT secret key consistency**

### High Error Rates

- **Database connection pool exhausted**: Increase pool size in backend config
- **Rate limiting**: Adjust rate limits for load testing
- **Memory issues**: Monitor backend memory usage
- **Network timeouts**: Increase `http_req_duration` threshold

### Low Throughput

- **Check backend logs**: Look for slow queries or bottlenecks
- **Database query optimization**: Add indexes for frequently queried fields
- **Caching**: Implement Redis caching for expensive operations
- **Connection reuse**: Ensure `noConnectionReuse: false` in options

## Best Practices

1. **Start small**: Run with 10-50 VUs first to establish baseline
2. **Warm up**: Include ramp-up period to avoid cold start issues
3. **Realistic scenarios**: Mix read/write operations based on actual usage
4. **Monitor backend**: Watch CPU, memory, database connections during tests
5. **Clean up**: Delete test data after load testing
6. **Document baselines**: Record expected metrics for comparison
7. **Schedule regularly**: Run load tests weekly to catch regressions

## Resources

- **k6 Documentation**: https://k6.io/docs/
- **k6 Cloud**: https://k6.io/cloud/
- **Grafana Dashboard**: https://grafana.com/grafana/dashboards/2587
- **Example Tests**: https://github.com/grafana/k6/tree/master/examples

## Support

For issues or questions:
- Check k6 documentation: https://k6.io/docs/
- Review backend logs: `docker-compose logs -f api worker`
- Open GitHub issue with test results and logs
