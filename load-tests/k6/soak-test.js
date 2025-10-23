/**
 * k6 Soak Test - Long Duration Stability Test
 *
 * Tests system stability over extended periods to detect:
 * - Memory leaks
 * - Resource exhaustion
 * - Performance degradation over time
 * - Connection pool issues
 *
 * Usage:
 *   k6 run soak-test.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { SharedArray } from 'k6/data';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

const TEST_USERS = new SharedArray('users', function () {
  return [
    { email: 'loadtest1@example.com', password: 'TestPass123!' },
    { email: 'loadtest2@example.com', password: 'TestPass123!' },
    { email: 'loadtest3@example.com', password: 'TestPass123!' },
  ];
});

const successRate = new Rate('successful_requests');
const throughput = new Counter('total_requests');
const responseDuration = new Trend('response_duration');

export const options = {
  scenarios: {
    soak_test: {
      executor: 'constant-vus',
      vus: 100,
      duration: '30m', // 30 minutes sustained load
    },
  },

  thresholds: {
    'http_req_duration': ['p(95)<3000', 'p(99)<5000'],
    'http_req_failed': ['rate<0.05'],
    'successful_requests': ['rate>0.95'],
    'response_duration': ['p(95)<3000'],
  },
};

function authenticate(user) {
  const loginRes = http.post(
    `${BASE_URL}${API_VERSION}/auth/login`,
    JSON.stringify(user),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  throughput.add(1);

  const success = check(loginRes, {
    'auth: status is 200': (r) => r.status === 200,
  });

  successRate.add(success);

  return success ? loginRes.json('access_token') : null;
}

export default function () {
  const user = TEST_USERS[__VU % TEST_USERS.length];
  const token = authenticate(user);

  if (!token) {
    sleep(2);
    return;
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  // Varied operations to simulate real usage
  group('Read Operations', function () {
    const startTime = Date.now();

    // Product list
    const listRes = http.get(
      `${BASE_URL}${API_VERSION}/tracking/products?limit=20`,
      { headers: headers }
    );

    responseDuration.add(Date.now() - startTime);
    throughput.add(1);

    successRate.add(check(listRes, {
      'products list: status is 200': (r) => r.status === 200,
    }));

    sleep(2);

    // Notifications
    const notifRes = http.get(
      `${BASE_URL}${API_VERSION}/notifications?limit=5`,
      { headers: headers }
    );

    throughput.add(1);

    successRate.add(check(notifRes, {
      'notifications: status is 200': (r) => r.status === 200,
    }));
  });

  sleep(3);

  group('Metrics Operations', function () {
    const metricsRes = http.get(
      `${BASE_URL}${API_VERSION}/metrics/summary?days=7`,
      { headers: headers }
    );

    throughput.add(1);

    successRate.add(check(metricsRes, {
      'metrics: status is 200 or 404': (r) => [200, 404].includes(r.status),
    }));
  });

  sleep(5); // Longer sleep to simulate user reading/analyzing data
}

export function setup() {
  console.log('='.repeat(80));
  console.log('k6 Soak Test - 30 Minute Stability Test');
  console.log('='.repeat(80));
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Virtual Users: 100`);
  console.log(`Duration: 30 minutes`);
  console.log('Testing for: Memory leaks, resource exhaustion, degradation');
  console.log('='.repeat(80));

  const healthRes = http.get(`${BASE_URL}/health`);

  if (healthRes.status !== 200) {
    throw new Error(`Health check failed: ${healthRes.status}`);
  }

  console.log('✅ Health check passed - Starting soak test...');

  return { startTime: Date.now() };
}

export function teardown(data) {
  const durationMin = ((Date.now() - data.startTime) / 1000 / 60).toFixed(2);

  console.log('='.repeat(80));
  console.log('Soak Test Completed');
  console.log('='.repeat(80));
  console.log(`Total Duration: ${durationMin} minutes`);
  console.log('Review metrics for performance degradation patterns');
  console.log('='.repeat(80));
}
