// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any interactive elements
    initializeChartResponsiveness();
});

function initializeChartResponsiveness() {
    // Make charts responsive
    const charts = document.querySelectorAll('[id$="-chart"]');
    charts.forEach(chart => {
        window.addEventListener('resize', function() {
            Plotly.Plots.resize(chart);
        });
    });
}

// Add smooth scrolling to all links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});
