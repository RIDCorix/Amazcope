/**
 * k6 Load Test Script - SLI-007: Throughput under 500 VUs
 *
 * Test Description:
 * - Measures successful requests per second under 500 concurrent virtual users
 * - Tests multiple API endpoints with realistic usage patterns
 * - Includes authentication and various CRUD operations
 *
 * SLI Target: Maintain high throughput (req/sec) with 500 VUs
 *
 * Usage:
 *   k6 run throughput-test.js
 *   k6 run --out json=results.json throughput-test.js
 *   k6 run --out influxdb=http://localhost:8086/k6 throughput-test.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { SharedArray } from 'k6/data';

// ============================================================================
// Configuration
// ============================================================================

// Base URL - Update this for your environment
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// Test credentials - create test users before running
const TEST_USERS = new SharedArray('users', function () {
  return [
    { email: 'loadtest1@example.com', password: 'TestPass123!' },
    { email: 'loadtest2@example.com', password: 'TestPass123!' },
    { email: 'loadtest3@example.com', password: 'TestPass123!' },
    { email: 'loadtest4@example.com', password: 'TestPass123!' },
    { email: 'loadtest5@example.com', password: 'TestPass123!' },
  ];
});

// ============================================================================
// Custom Metrics
// ============================================================================

const successRate = new Rate('successful_requests');
const throughput = new Counter('total_requests');
const authDuration = new Trend('auth_duration');
const productListDuration = new Trend('product_list_duration');
const productDetailDuration = new Trend('product_detail_duration');
const metricsDuration = new Trend('metrics_duration');
const notificationsDuration = new Trend('notifications_duration');

// ============================================================================
// Test Configuration - 500 VUs for SLI-007
// ============================================================================

export const options = {
  scenarios: {
    // Scenario 1: Steady load with 500 VUs
    steady_load: {
      executor: 'constant-vus',
      vus: 500,
      duration: '10s',
      tags: { scenario: 'steady_load' },
    },

    // Scenario 2: Ramping load to test throughput degradation
    ramping_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '5s', target: 100 },
        { duration: '5s', target: 250 },
        { duration: '5s', target: 500 },
        { duration: '5s', target: 500 }, // Sustained 500 VUs
        { duration: '5s', target: 0 },
      ],
      startTime: '10s', // Start after steady_load completes
      tags: { scenario: 'ramping_load' },
    },
  },

  thresholds: {
    // Throughput thresholds
    'total_requests': ['count>10000'], // Minimum 10k requests over test duration
    'successful_requests': ['rate>0.95'], // 95% success rate minimum

    // Response time thresholds
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'], // 95th percentile < 2s, 99th < 5s
    'http_req_duration{scenario:steady_load}': ['p(95)<2000'],
    'http_req_duration{scenario:ramping_load}': ['p(95)<3000'],

    // Specific endpoint thresholds
    'auth_duration': ['p(95)<1000'], // Auth should be fast
    'product_list_duration': ['p(95)<2000'],
    'product_detail_duration': ['p(95)<1500'],
    'metrics_duration': ['p(95)<3000'],
    'notifications_duration': ['p(95)<1000'],

    // Error rate thresholds
    'http_req_failed': ['rate<0.05'], // Less than 5% failures
  },

  // Global test settings
  noConnectionReuse: false,
  userAgent: 'k6-load-test/1.0 (SLI-007-throughput)',
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get or refresh authentication token
 */
function authenticate(user) {
  const startTime = Date.now();

  const loginRes = http.post(
    `${BASE_URL}${API_VERSION}/auth/login`,
    JSON.stringify({
      email_or_username: user.email,
      password: user.password,
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { endpoint: 'auth/login' },
    }
  );

  authDuration.add(Date.now() - startTime);
  throughput.add(1);

  const success = check(loginRes, {
    'auth: status is 200': (r) => r.status === 200,
    'auth: has access token': (r) => r.json('access_token') !== undefined,
  });

  successRate.add(success);

  if (success) {
    return loginRes.json('access_token');
  }

  return null;
}

/**
 * Create authorization headers
 */
function authHeaders(token) {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
}

/**
 * Random integer between min and max (inclusive)
 */
function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Random item from array
 */
function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

// ============================================================================
// Test Scenarios
// ============================================================================

export default function () {
  // Select a random user for this VU
  const user = TEST_USERS[__VU % TEST_USERS.length];

  // Authenticate
  const token = authenticate(user);
  if (!token) {
    sleep(1);
    return;
  }

  const headers = authHeaders(token);

  // ========================================================================
  // Test Group 1: Product Tracking (Most Common Operations)
  // ========================================================================

  group('Product Tracking Operations', function () {
    // List user's products
    const startTime1 = Date.now();
    const listRes = http.get(
      `${BASE_URL}${API_VERSION}/tracking/products?skip=0&limit=20`,
      {
        headers: headers,
        tags: { endpoint: 'tracking/products', operation: 'list' },
      }
    );
    productListDuration.add(Date.now() - startTime1);
    throughput.add(1);

    const listSuccess = check(listRes, {
      'products list: status is 200': (r) => r.status === 200,
      'products list: is array': (r) => Array.isArray(r.json()),
    });
    successRate.add(listSuccess);

    // Get product details (if products exist)
    if (listSuccess && listRes.json().length > 0) {
      const randomProduct = randomItem(listRes.json());

      const startTime2 = Date.now();
      const detailRes = http.get(
        `${BASE_URL}${API_VERSION}/tracking/products/${randomProduct.id}`,
        {
          headers: headers,
          tags: { endpoint: 'tracking/products/{id}', operation: 'detail' },
        }
      );
      productDetailDuration.add(Date.now() - startTime2);
      throughput.add(1);

      const detailSuccess = check(detailRes, {
        'product detail: status is 200': (r) => r.status === 200,
        'product detail: has id': (r) => r.json('id') !== undefined,
      });
      successRate.add(detailSuccess);
    }
  });

  sleep(randomInt(1, 2)); // Simulate user think time

  // ========================================================================
  // Test Group 2: Metrics Retrieval
  // ========================================================================

  group('Metrics Operations', function () {
    // Get metrics summary
    const startTime = Date.now();
    const metricsRes = http.get(
      `${BASE_URL}${API_VERSION}/metrics/summary?days=30`,
      {
        headers: headers,
        tags: { endpoint: 'metrics/summary', operation: 'get' },
      }
    );
    metricsDuration.add(Date.now() - startTime);
    throughput.add(1);

    const success = check(metricsRes, {
      'metrics: status is 200 or 404': (r) => [200, 404].includes(r.status),
    });
    successRate.add(success);
  });

  sleep(randomInt(1, 3));

  // ========================================================================
  // Test Group 3: Notifications
  // ========================================================================

  group('Notification Operations', function () {
    // List notifications
    const startTime = Date.now();
    const notifRes = http.get(
      `${BASE_URL}${API_VERSION}/notifications?skip=0&limit=10`,
      {
        headers: headers,
        tags: { endpoint: 'notifications', operation: 'list' },
      }
    );
    notificationsDuration.add(Date.now() - startTime);
    throughput.add(1);

    const success = check(notifRes, {
      'notifications: status is 200': (r) => r.status === 200,
    });
    successRate.add(success);
  });

  sleep(randomInt(1, 2));

  // ========================================================================
  // Test Group 4: User Settings (Lighter Load)
  // ========================================================================

  if (randomInt(1, 100) <= 20) { // Only 20% of VUs check settings
    group('User Settings', function () {
      const settingsRes = http.get(
        `${BASE_URL}${API_VERSION}/user/settings`,
        {
          headers: headers,
          tags: { endpoint: 'user/settings', operation: 'get' },
        }
      );
      throughput.add(1);

      const success = check(settingsRes, {
        'settings: status is 200': (r) => r.status === 200,
      });
      successRate.add(success);
    });
  }

  sleep(randomInt(2, 4));

  // ========================================================================
  // Test Group 5: Optimization Suggestions (Occasional)
  // ========================================================================

  if (randomInt(1, 100) <= 15) { // Only 15% of VUs request optimization
    group('Optimization Operations', function () {
      const optimRes = http.get(
        `${BASE_URL}${API_VERSION}/optimization/suggestions?limit=5`,
        {
          headers: headers,
          tags: { endpoint: 'optimization/suggestions', operation: 'list' },
        }
      );
      throughput.add(1);

      const success = check(optimRes, {
        'optimization: status is 200 or 404': (r) => [200, 404].includes(r.status),
      });
      successRate.add(success);
    });
  }

  sleep(randomInt(1, 3));
}

// ============================================================================
// Test Lifecycle Hooks
// ============================================================================

export function setup() {
  console.log('='.repeat(80));
  console.log('k6 Load Test: SLI-007 Throughput Test - 500 VUs');
  console.log('='.repeat(80));
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`API Version: ${API_VERSION}`);
  console.log(`Test Users: ${TEST_USERS.length}`);
  console.log('='.repeat(80));

  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);

  if (healthRes.status !== 200) {
    throw new Error(`Health check failed: ${healthRes.status}`);
  }

  console.log('✅ Health check passed');
  console.log('Starting load test...');
  console.log('='.repeat(80));

  return { timestamp: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.timestamp) / 1000;

  console.log('='.repeat(80));
  console.log('Load Test Completed');
  console.log('='.repeat(80));
  console.log(`Total Duration: ${duration.toFixed(2)}s`);
  console.log('='.repeat(80));
}
