/**
 * main.js
 *
 * This file contains general JavaScript functionalities, event listeners,
 * and UI interactions for the application. It leverages jQuery for DOM manipulation
 * and AJAX requests, and integrates with Bootstrap 5 components and Chart.js
 * for interactive data visualizations.
 *
 * Author: Google Standard Senior Python Developer
 * Date: 2023-10-27
 */

// Use an IIFE (Immediately Invoked Function Expression) to encapsulate the code
// and avoid polluting the global namespace.
(function($) {
    "use strict"; // Enforce stricter parsing and error handling

    // --- Global Constants and Selectors ---
    const API_BASE_URL = '/api'; // Base URL for API endpoints
    const TOAST_CONTAINER_SELECTOR = '#toast-container';
    const LOADING_INDICATOR_SELECTOR = '#loading-indicator'; // Assuming a loading spinner/overlay exists in base template

    // --- Utility Functions ---

    /**
     * Displays a Bootstrap Toast notification to the user.
     * @param {string} message - The message to display in the toast.
     * @param {'success'|'error'|'info'|'warning'} type - The type of toast (determines styling).
     * @param {number} [delay=5000] - The delay in milliseconds before the toast auto-hides.
     */
    function showToast(message, type = 'info', delay = 5000) {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="${delay}">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        let $toastContainer = $(TOAST_CONTAINER_SELECTOR);
        if ($toastContainer.length === 0) {
            console.warn("Toast container not found. Appending a default one.");
            $('body').append('<div id="toast-container" class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 1080;"></div>');
            $toastContainer = $(TOAST_CONTAINER_SELECTOR);
        }
        const $toast = $(toastHtml);
        $toastContainer.append($toast);
        const bsToast = new bootstrap.Toast($toast[0]);
        bsToast.show();
    }

    /**
     * Shows a global loading indicator (e.g., spinner overlay).
     * Assumes a div with id `loading-indicator` that can be toggled with `d-none` and `d-flex`.
     */
    function showLoadingIndicator() {
        $(LOADING_INDICATOR_SELECTOR).removeClass('d-none').addClass('d-flex');
    }

    /**
     * Hides the global loading indicator.
     * Assumes a div with id `loading-indicator` that can be toggled with `d-none` and `d-flex`.
     */
    function hideLoadingIndicator() {
        $(LOADING_INDICATOR