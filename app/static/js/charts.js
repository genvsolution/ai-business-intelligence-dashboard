/**
 * app/static/js/charts.js
 *
 * This JavaScript file is dedicated to handling Chart.js configurations,
 * data fetching for charts, and interactive chart behaviors within the
 * sales analytics dashboard.
 *
 * It leverages jQuery for DOM manipulation and AJAX requests, and Chart.js
 * for rendering various interactive data visualizations.
 *
 * Author: Senior Python Developer (Google Standard)
 * Date: 2023-10-27
 */

// Ensure jQuery is loaded before proceeding
if (typeof jQuery === 'undefined') {
    console.error('jQuery is not loaded. Chart.js functionality may be impaired.');
}

// Global object to store chart instances for easy access and updates
const chartInstances = {};

// --- Chart.js Global Defaults Configuration ---
/**
 * Configures global settings for Chart.js to ensure consistent styling
 * and behavior across all charts. This includes responsiveness, font settings,
 * and default tooltip/legend behaviors.
 */
function configureChartJsDefaults() {
    // Set global Chart.js options
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false; // Allow charts to fill their containers
    Chart.defaults.font.family = 'Inter, "Helvetica Neue", Arial, sans-serif'; // Consistent font
    Chart.defaults.color = '#6c757d'; // Default text color (Bootstrap secondary)

    // Tooltip defaults for better readability and consistency
    Chart.defaults.plugins.tooltip.mode = 'index';
    Chart.defaults.plugins.tooltip.intersect = false; // Show tooltip for nearest items
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    Chart.defaults.plugins.tooltip.titleFont = { weight: 'bold' };
    Chart.defaults.plugins.tooltip.bodyFont = { size: 14 };
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 4;

    // Legend defaults for consistent positioning and label styling
    Chart.defaults.plugins