/**
 * k6 Spike Test - Sudden Traffic Surge
 *
 * Tests system behavior under sudden traffic spikes to validate:
 * - Auto-scaling capabilities
 * - Error handling under extreme load
 * - Recovery after spike subsides
 *
 * Usage:
 *   k6 run spike-test.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

const successRate = new Rate('successful_requests');
const throughput = new Counter('total_requests');

export const options = {
  scenarios: {
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Normal load
        { duration: '30s', target: 1000 }, // Sudden spike!
        { duration: '3m', target: 1000 },  // Sustained spike
        { duration: '2m', target: 50 },    // Recovery
        { duration: '2m', target: 0 },     // Cool down
      ],
    },
  },

  thresholds: {
    'http_req_duration': ['p(95)<5000'], // More lenient during spike
    'http_req_failed': ['rate<0.15'],    // Allow up to 15% failures during spike
    'successful_requests': ['rate>0.85'],
  },
};

const TEST_USER = {
  email: 'loadtest1@example.com',
  password: 'TestPass123!',
};

function authenticate() {
  const loginRes = http.post(
    `${BASE_URL}${API_VERSION}/auth/login`,
    JSON.stringify(TEST_USER),
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
  const token = authenticate();
  if (!token) {
    sleep(1);
    return;
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  // Simple product list request
  const res = http.get(
    `${BASE_URL}${API_VERSION}/tracking/products?limit=10`,
    { headers: headers }
  );

  throughput.add(1);

  const success = check(res, {
    'products: status is 200': (r) => r.status === 200,
  });

  successRate.add(success);

  sleep(1);
}

export function setup() {
  console.log('Starting Spike Test - Sudden Traffic Surge');
  console.log(`Base URL: ${BASE_URL}`);
  console.log('Spike Pattern: 50 → 1000 VUs in 30 seconds');
}
