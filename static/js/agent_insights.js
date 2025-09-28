// Agent Integration and Tooltips
class AgentInsights {
    constructor() {
        this.tooltips = {};
        this.alerts = [];
        this.recommendations = [];
        this.updateInterval = 60000; // Update every minute
    }

    async init() {
        await this.fetchInsights();
        this.setupTooltips();
        this.setupAlertBadge();
        setInterval(() => this.fetchInsights(), this.updateInterval);
    }

    async fetchInsights() {
        try {
            const response = await fetch('/api/insights');
            if (!response.ok) throw new Error('Failed to fetch insights');
            
            const data = await response.json();
            this.tooltips = data.tooltips || {};
            this.alerts = data.alerts || [];
            this.recommendations = data.recommendations || [];
            
            this.updateUI();
        } catch (error) {
            console.error('Error fetching insights:', error);
        }
    }

    setupTooltips() {
        // Initialize tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        this.tooltipInstances = [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
    }

    setupAlertBadge() {
        // Create alert badge if it doesn't exist
        if (!document.getElementById('agent-alert-badge')) {
            const badge = document.createElement('div');
            badge.id = 'agent-alert-badge';
            badge.className = 'position-fixed top-0 end-0 p-3';
            document.body.appendChild(badge);
        }
    }

    updateUI() {
        // Update tooltips
        this.tooltips.forEach(tooltip => {
            const element = document.getElementById(tooltip.element_id);
            if (element) {
                element.setAttribute('data-bs-toggle', 'tooltip');
                element.setAttribute('data-bs-placement', tooltip.position || 'top');
                element.setAttribute('title', tooltip.message);
                
                // Refresh tooltip instance
                const tooltipInstance = bootstrap.Tooltip.getInstance(element);
                if (tooltipInstance) {
                    tooltipInstance.dispose();
                }
                new bootstrap.Tooltip(element);
            }
        });

        // Update alerts
        if (this.alerts.length > 0) {
            const badge = document.getElementById('agent-alert-badge');
            badge.innerHTML = this.alerts.map(alert => `
                <div class="toast show" role="alert">
                    <div class="toast-header">
                        <strong class="me-auto">EcoAgent Alert</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">
                        ${alert.message}
                        <div class="mt-2 pt-2 border-top">
                            <small class="text-muted">${alert.tooltip}</small>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }
}

// Initialize agent insights when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const insights = new AgentInsights();
    insights.init();
});
