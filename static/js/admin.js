document.addEventListener('DOMContentLoaded', function() {
    const responseArea = document.getElementById('response');
    
    // Load statistics on page load
    loadStatistics();
    
    // Health check button
    document.getElementById('healthCheck').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            responseArea.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            responseArea.textContent = `Error: ${error.message}`;
        }
    });
    
    // Get documents button
    document.getElementById('getDocuments').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/documents');
            const data = await response.json();
            responseArea.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            responseArea.textContent = `Error: ${error.message}`;
        }
    });
    
    // Get migration logs button
    document.getElementById('getLogs').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/migration-logs');
            const data = await response.json();
            responseArea.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            responseArea.textContent = `Error: ${error.message}`;
        }
    });
    
    // Import dump button
    document.getElementById('importDump').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/import-dump', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            responseArea.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            responseArea.textContent = `Error: ${error.message}`;
        }
    });
    
    // Refresh statistics button
    document.getElementById('refreshStats').addEventListener('click', function() {
        loadStatistics();
    });
    
    // Clear response button
    document.getElementById('clearResponse').addEventListener('click', function() {
        responseArea.textContent = 'Ready to make API calls...';
    });
    
    // Export response button
    document.getElementById('exportResponse').addEventListener('click', function() {
        const content = responseArea.textContent;
        if (content && content !== 'Ready to make API calls...') {
            try {
                const blob = new Blob([content], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'api-response.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Export failed:', error);
            }
        }
    });
    
    // Load statistics function
    async function loadStatistics() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.status === 'success') {
                const stats = data.statistics.documents;
                document.getElementById('totalDocs').textContent = stats.total;
                document.getElementById('pendingDocs').textContent = stats.pending;
                document.getElementById('migratedDocs').textContent = stats.migrated;
                document.getElementById('failedDocs').textContent = stats.failed || 0;
            }
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }
    
    // Add some interactive effects
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 20px 40px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 10px 30px rgba(0,0,0,0.1)';
        });
    });
    
    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.textContent;
            this.textContent = 'Loading...';
            this.disabled = true;
            
            setTimeout(() => {
                this.textContent = originalText;
                this.disabled = false;
            }, 1000);
        });
    });
    
    // Auto-refresh statistics every 30 seconds
    setInterval(loadStatistics, 30000);
}); 