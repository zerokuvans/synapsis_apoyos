// Main JavaScript entry point for Synapsis Apoyos
import 'bootstrap';
import '../css/main.scss';

// Import modules
import { initializeDataTables } from './modules/datatables';
import { initializeCharts } from './modules/charts';
import { initializeFormValidation } from './modules/forms';
import { initializeNotifications } from './modules/notifications';
import { initializeModals } from './modules/modals';
import { initializeTooltips } from './modules/tooltips';
import { initializeSelect2 } from './modules/select2';
import { initializeFileUpload } from './modules/fileupload';
import { initializeTheme } from './modules/theme';

// Global app object
window.SynapsisApp = {
  version: '1.0.0',
  debug: process.env.NODE_ENV === 'development',
  
  // Initialize all modules
  init() {
    console.log('Initializing Synapsis Apoyos Application...');
    
    try {
      // Initialize core modules
      initializeTheme();
      initializeTooltips();
      initializeModals();
      initializeNotifications();
      
      // Initialize form modules
      initializeFormValidation();
      initializeSelect2();
      initializeFileUpload();
      
      // Initialize data modules
      initializeDataTables();
      initializeCharts();
      
      console.log('Application initialized successfully');
    } catch (error) {
      console.error('Error initializing application:', error);
    }
  },
  
  // Utility functions
  utils: {
    // Format currency
    formatCurrency(amount) {
      return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP'
      }).format(amount);
    },
    
    // Format date
    formatDate(date, options = {}) {
      const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      };
      return new Intl.DateTimeFormat('es-CL', { ...defaultOptions, ...options }).format(new Date(date));
    },
    
    // Debounce function
    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },
    
    // Show loading state
    showLoading(element) {
      if (element) {
        element.classList.add('loading');
        element.disabled = true;
      }
    },
    
    // Hide loading state
    hideLoading(element) {
      if (element) {
        element.classList.remove('loading');
        element.disabled = false;
      }
    },
    
    // AJAX helper
    async request(url, options = {}) {
      const defaultOptions = {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      };
      
      try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
      } catch (error) {
        console.error('Request failed:', error);
        throw error;
      }
    }
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.SynapsisApp.init();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    console.log('Page hidden');
  } else {
    console.log('Page visible');
  }
});

// Handle online/offline status
window.addEventListener('online', () => {
  console.log('Connection restored');
  // Show notification or update UI
});

window.addEventListener('offline', () => {
  console.log('Connection lost');
  // Show notification or update UI
});

// Export for use in other modules
export default window.SynapsisApp;