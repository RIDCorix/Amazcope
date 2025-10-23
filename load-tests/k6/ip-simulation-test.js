/**
 * k6 Load Test Script - Enhanced with IP Simulation
 *
 * Features:
 * - Simulates requests from different IP addresses
 * - Tests rate limiting and IP-based features
 * - Measures throughput under 500 VUs with diverse IPs
 *
 * IP Simulation Methods:
 * 1. X-Forwarded-For header (simulates proxy/load balancer)
 * 2. X-Real-IP header (common in nginx setups)
 * 3. Random IP generation for each VU
 *
 * Usage:
 *   k6 run ip-simulation-test.js
 *   k6 run --env SIMULATE_IPS=true ip-simulation-test.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { SharedArray } from 'k6/data';

// ============================================================================
// Configuration
// ============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';
const SIMULATE_IPS = __ENV.SIMULATE_IPS === 'true' || true; // Enable IP simulation

// Test credentials
const TEST_USERS = new SharedArray('users', function () {
  return [
    { email: 'loadtest1@example.com', password: 'TestPass123!' },
    { email: 'loadtest2@example.com', password: 'TestPass123!' },
    { email: 'loadtest3@example.com', password: 'TestPass123!' },
    { email: 'loadtest4@example.com', password: 'TestPass123!' },
    { email: 'loadtest5@example.com', password: 'TestPass123!' },
  ];
});

// IP address pools for simulation
const IP_POOLS = {
  // Simulate traffic from different geographic regions
  north_america: [
    '192.168.1.', '192.168.2.', '10.0.0.', '10.0.1.',
    '172.16.0.', '172.16.1.', '204.79.197.', '157.55.39.',
  ],
  europe: [
    '192.168.10.', '192.168.20.', '10.10.0.', '10.20.0.',
    '172.20.0.', '172.21.0.', '51.124.', '52.232.',
  ],
  asia: [
    '192.168.100.', '192.168.200.', '10.100.0.', '10.200.0.',
    '172.30.0.', '172.31.0.', '13.75.', '52.175.',
  ],
  mobile_carriers: [
    '100.64.', '100.65.', '100.66.', // Carrier-grade NAT
  ],
};

// ============================================================================
// Custom Metrics
// ============================================================================

const successRate = new Rate('successful_requests');
const throughput = new Counter('total_requests');
const ipDistribution = new Counter('unique_ips_used');
const rateLimitHits = new Counter('rate_limit_hits');
const authDuration = new Trend('auth_duration');
const productListDuration = new Trend('product_list_duration');

// ============================================================================
// Test Configuration
// ============================================================================

export const options = {
  scenarios: {
    steady_load: {
      executor: 'constant-vus',
      vus: 500,
      duration: '5m',
      tags: { scenario: 'steady_load' },
    },
  },

  thresholds: {
    'total_requests': ['count>10000'],
    'successful_requests': ['rate>0.95'],
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],
    'http_req_failed': ['rate<0.05'],
    'rate_limit_hits': ['count<100'], // Track rate limiting
  },
};

// ============================================================================
// IP Simulation Functions
// ============================================================================

/**
 * Generate a random IP address from a specific region
 * @param {string} region - Region name (north_america, europe, asia, mobile_carriers)
 * @returns {string} Random IP address
 */
function generateRandomIP(region = 'north_america') {
  const pool = IP_POOLS[region] || IP_POOLS.north_america;
  const prefix = pool[Math.floor(Math.random() * pool.length)];

  // Complete the IP with random octets
  if (prefix.split('.').length === 3) {
    // Prefix like "192.168.1." - add last octet
    return prefix + Math.floor(Math.random() * 254 + 1);
  } else if (prefix.split('.').length === 2) {
    // Prefix like "51.124." - add two octets
    return prefix + Math.floor(Math.random() * 255) + '.' + Math.floor(Math.random() * 254 + 1);
  }

  return prefix + '0.1'; // Fallback
}

/**
 * Generate IP based on VU number (deterministic)
 * Useful for testing rate limiting per IP
 * @param {number} vuNumber - Virtual user number
 * @returns {string} IP address
 */
function generateIPForVU(vuNumber) {
  const subnet = Math.floor(vuNumber / 254);
  const host = (vuNumber % 254) + 1;
  return `192.168.${subnet}.${host}`;
}

/**
 * Select random region based on distribution
 * Simulates realistic geographic traffic distribution
 * @returns {string} Region name
 */
function selectRandomRegion() {
  const rand = Math.random();

  // Weighted distribution: 50% NA, 30% EU, 15% Asia, 5% Mobile
  if (rand < 0.50) return 'north_america';
  if (rand < 0.80) return 'europe';
  if (rand < 0.95) return 'asia';
  return 'mobile_carriers';
}

/**
 * Create headers with simulated IP address
 * @param {string} ip - IP address to simulate
 * @param {string} token - JWT token (optional)
 * @returns {object} HTTP headers
 */
function createHeadersWithIP(ip, token = null) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Forwarded-For': ip,       // Standard proxy header
    'X-Real-IP': ip,              // Nginx/alternative header
    'X-Client-IP': ip,            // Some CDNs use this
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Authenticate user with simulated IP
 */
function authenticate(user, clientIP) {
  const startTime = Date.now();

  const loginRes = http.post(
    `${BASE_URL}${API_VERSION}/auth/login`,
    JSON.stringify({
      email_or_username: user.email,
      password: user.password,
    }),
    {
      headers: createHeadersWithIP(clientIP),
      tags: { endpoint: 'auth/login', client_ip: clientIP },
    }
  );

  authDuration.add(Date.now() - startTime);
  throughput.add(1);

  const success = check(loginRes, {
    'auth: status is 200': (r) => r.status === 200,
    'auth: has access token': (r) => r.json('access_token') !== undefined,
  });

  successRate.add(success);

  // Track rate limiting
  if (loginRes.status === 429) {
    rateLimitHits.add(1);
  }

  if (success) {
    return loginRes.json('access_token');
  }

  return null;
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

  // IP Simulation Strategy - Choose one:

  // Strategy 1: Random IP per VU (simulates distributed users)
  const region = selectRandomRegion();
  const clientIP = generateRandomIP(region);

  // Strategy 2: Deterministic IP per VU (useful for rate limit testing)
  // const clientIP = generateIPForVU(__VU);

  // Strategy 3: Random IP per iteration (simulates mobile users changing IPs)
  // const clientIP = generateRandomIP(selectRandomRegion());

  // Track unique IPs used
  ipDistribution.add(1);

  // Authenticate with simulated IP
  const token = authenticate(user, clientIP);
  if (!token) {
    sleep(1);
    return;
  }

  const headers = createHeadersWithIP(clientIP, token);

  // ========================================================================
  // Test Group 1: Product Tracking
  // ========================================================================

  group('Product Tracking Operations', function () {
    // List user's products
    const startTime1 = Date.now();
    const listRes = http.get(
      `${BASE_URL}${API_VERSION}/tracking/products?skip=0&limit=20`,
      {
        headers: headers,
        tags: {
          endpoint: 'tracking/products',
          operation: 'list',
          client_ip: clientIP,
          region: region,
        },
      }
    );
    productListDuration.add(Date.now() - startTime1);
    throughput.add(1);

    const listSuccess = check(listRes, {
      'products list: status is 200': (r) => r.status === 200,
      'products list: is array': (r) => Array.isArray(r.json()),
    });
    successRate.add(listSuccess);

    // Track rate limiting
    if (listRes.status === 429) {
      rateLimitHits.add(1);
    }

    // Get product details (if products exist)
    if (listSuccess && listRes.json().length > 0) {
      const randomProduct = randomItem(listRes.json());

      const detailRes = http.get(
        `${BASE_URL}${API_VERSION}/tracking/products/${randomProduct.id}`,
        {
          headers: headers,
          tags: {
            endpoint: 'tracking/products/{id}',
            operation: 'detail',
            client_ip: clientIP,
          },
        }
      );
      throughput.add(1);

      const detailSuccess = check(detailRes, {
        'product detail: status is 200': (r) => r.status === 200,
        'product detail: has id': (r) => r.json('id') !== undefined,
      });
      successRate.add(detailSuccess);

      if (detailRes.status === 429) {
        rateLimitHits.add(1);
      }
    }
  });

  sleep(randomInt(1, 2));

  // ========================================================================
  // Test Group 2: Metrics Retrieval
  // ========================================================================

  group('Metrics Operations', function () {
    const metricsRes = http.get(
      `${BASE_URL}${API_VERSION}/metrics/summary?days=30`,
      {
        headers: headers,
        tags: {
          endpoint: 'metrics/summary',
          operation: 'get',
          client_ip: clientIP,
        },
      }
    );
    throughput.add(1);

    const success = check(metricsRes, {
      'metrics: status is 200 or 404': (r) => [200, 404].includes(r.status),
    });
    successRate.add(success);

    if (metricsRes.status === 429) {
      rateLimitHits.add(1);
    }
  });

  sleep(randomInt(1, 3));

  // ========================================================================
  // Test Group 3: Notifications
  // ========================================================================

  group('Notification Operations', function () {
    const notifRes = http.get(
      `${BASE_URL}${API_VERSION}/notifications?skip=0&limit=10`,
      {
        headers: headers,
        tags: {
          endpoint: 'notifications',
          operation: 'list',
          client_ip: clientIP,
        },
      }
    );
    throughput.add(1);

    const success = check(notifRes, {
      'notifications: status is 200': (r) => r.status === 200,
    });
    successRate.add(success);

    if (notifRes.status === 429) {
      rateLimitHits.add(1);
    }
  });

  sleep(randomInt(2, 4));
}

// ============================================================================
// Test Lifecycle Hooks
// ============================================================================

export function setup() {
  console.log('='.repeat(80));
  console.log('k6 Load Test: IP Simulation Test - 500 VUs');
  console.log('='.repeat(80));
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`API Version: ${API_VERSION}`);
  console.log(`IP Simulation: ${SIMULATE_IPS ? 'ENABLED' : 'DISABLED'}`);
  console.log(`Test Users: ${TEST_USERS.length}`);
  console.log('');
  console.log('IP Simulation Strategy:');
  console.log('  - Random IPs from multiple regions');
  console.log('  - Geographic distribution: 50% NA, 30% EU, 15% Asia, 5% Mobile');
  console.log('  - Headers: X-Forwarded-For, X-Real-IP, X-Client-IP');
  console.log('='.repeat(80));

  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);

  if (healthRes.status !== 200) {
    throw new Error(`Health check failed: ${healthRes.status}`);
  }

  console.log('✅ Health check passed');
  console.log('Starting load test with IP simulation...');
  console.log('='.repeat(80));

  return { timestamp: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.timestamp) / 1000;

  console.log('='.repeat(80));
  console.log('Load Test Completed');
  console.log('='.repeat(80));
  console.log(`Total Duration: ${duration.toFixed(2)}s`);
  console.log('');
  console.log('Check metrics for:');
  console.log('  - unique_ips_used: Number of unique IPs simulated');
  console.log('  - rate_limit_hits: Times rate limiting was triggered');
  console.log('='.repeat(80));
}
