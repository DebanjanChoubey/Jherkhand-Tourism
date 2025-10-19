// API helper functions for frontend
const API_BASE_URL = '';

// Generic API request function
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const config = { ...defaultOptions, ...options };
  
  try {
    const response = await fetch(url, config);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || `HTTP error! status: ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Health check
export async function checkHealth() {
  return apiRequest('/api/health');
}

// Destinations
export async function getDestinations() {
  return apiRequest('/api/destinations');
}

// Events
export async function getEvents() {
  return apiRequest('/api/events');
}

// Providers
export async function getProviders() {
  return apiRequest('/api/providers');
}

// Feedback
export async function submitFeedback(feedbackData) {
  return apiRequest('/api/feedback', {
    method: 'POST',
    body: JSON.stringify(feedbackData)
  });
}

export async function getFeedback(limit = 10) {
  return apiRequest(`/api/feedback?limit=${limit}`);
}

// Payments
export async function createOrder(orderData) {
  return apiRequest('/api/payments/create-order', {
    method: 'POST',
    body: JSON.stringify(orderData)
  });
}

export async function verifyPayment(paymentData) {
  return apiRequest('/api/payments/verify-payment', {
    method: 'POST',
    body: JSON.stringify(paymentData)
  });
}

// Authentication
export async function login(credentials) {
  return apiRequest('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials)
  });
}

export async function register(userData) {
  return apiRequest('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData)
  });
}

// Admin functions
export async function getDashboardStats() {
  const token = localStorage.getItem('adminToken');
  return apiRequest('/api/admin/dashboard-stats', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
}

export async function getPayments() {
  const token = localStorage.getItem('adminToken');
  return apiRequest('/api/admin/payments', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
}

export async function issueCertificate(certificateData) {
  const token = localStorage.getItem('adminToken');
  return apiRequest('/api/admin/certificates/issue', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(certificateData)
  });
}
