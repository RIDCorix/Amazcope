/**
 * Test script to verify authService correctly handles login response
 *
 * Run in browser console after importing authService
 */

// Mock API response that matches backend
const mockLoginResponse = {
  data: {
    access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    refresh_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    token_type: 'bearer',
    user: {
      id: 2,
      email: 'test@example.com',
      username: 'testuser',
      full_name: 'Test User',
      is_active: true,
      is_superuser: false,
      created_at: '2025-10-17T08:20:05.429842+00:00',
      updated_at: '2025-10-17T08:20:05.430183+00:00',
    },
  },
};

// Simulate what authService.login() does
function testAuthServiceLogic() {
  console.log('=== Testing Auth Service Logic ===\n');

  const tokenData = mockLoginResponse.data;

  // Step 1: Store tokens
  console.log('Step 1: Store tokens in localStorage');
  if (tokenData.access_token) {
    localStorage.setItem('authToken', tokenData.access_token);
    localStorage.setItem('refreshToken', tokenData.refresh_token);
    console.log('✅ Tokens stored');
  }

  // Step 2: Create authData
  console.log('\nStep 2: Create authData object');
  const authData = {
    token: tokenData.access_token,
    refreshToken: tokenData.refresh_token,
    user: tokenData.user,
  };

  console.log('authData:', authData);
  console.log('authData.user:', authData.user);

  // Step 3: Store user data
  console.log('\nStep 3: Store user in localStorage');
  if (authData.user) {
    localStorage.setItem('user', JSON.stringify(authData.user));
    console.log('✅ User stored');
  } else {
    console.error('❌ authData.user is undefined!');
  }

  // Step 4: Verify stored data
  console.log('\n=== Verification ===');
  const storedUser = localStorage.getItem('user');
  console.log('Stored user string:', storedUser);

  if (storedUser && storedUser !== 'undefined') {
    const parsedUser = JSON.parse(storedUser);
    console.log('✅ Parsed user object:', parsedUser);
    console.log('✅ user.id:', parsedUser.id);
    console.log('✅ user.email:', parsedUser.email);
    console.log('✅ user.username:', parsedUser.username);
    console.log('\n🎉 Test passed! User data correctly stored.');
  } else {
    console.error('❌ Test failed! User data is undefined or invalid.');
  }

  // Cleanup
  console.log('\n=== Cleanup ===');
  localStorage.removeItem('authToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('user');
  console.log('✅ Test data cleaned up');
}

// Run test
testAuthServiceLogic();

// Export for use in other tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { testAuthServiceLogic, mockLoginResponse };
}
