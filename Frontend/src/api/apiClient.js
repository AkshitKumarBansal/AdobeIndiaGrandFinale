import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.MODE === 'production' ? '' : 'http://localhost:8000',
});

// Function to set the authorization token for all subsequent requests
export const setAuthToken = (token) => {
  if (token) {
    // Add the 'Bearer ' prefix required by FastAPI
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

export default apiClient;