/**
 * AgTools Mobile Web App - Core JavaScript
 * v2.6.0 Phase 6
 */

(function() {
    'use strict';

    // ========================================================================
    // OFFLINE DETECTION
    // ========================================================================

    const offlineBanner = document.getElementById('offline-banner');

    function updateOnlineStatus() {
        if (offlineBanner) {
            if (navigator.onLine) {
                offlineBanner.classList.remove('visible');
            } else {
                offlineBanner.classList.add('visible');
            }
        }
    }

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Check initial status
    updateOnlineStatus();

    // ========================================================================
    // FORM ENHANCEMENTS
    // ========================================================================

    // Prevent double-submit on forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner"></span> Please wait...';
            }
        });
    });

    // ========================================================================
    // TOUCH ENHANCEMENTS
    // ========================================================================

    // Add touch feedback to clickable elements
    document.querySelectorAll('.task-card, .btn').forEach(el => {
        el.addEventListener('touchstart', function() {
            this.classList.add('touch-active');
        });
        el.addEventListener('touchend', function() {
            this.classList.remove('touch-active');
        });
        el.addEventListener('touchcancel', function() {
            this.classList.remove('touch-active');
        });
    });

    // ========================================================================
    // UTILITY FUNCTIONS
    // ========================================================================

    window.AgTools = {
        // Show a toast notification
        toast: function(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);

            setTimeout(() => toast.classList.add('visible'), 10);
            setTimeout(() => {
                toast.classList.remove('visible');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        },

        // Confirm action
        confirm: function(message) {
            return window.confirm(message);
        }
    };

})();
