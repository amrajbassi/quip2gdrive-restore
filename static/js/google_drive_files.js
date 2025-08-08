document.addEventListener('DOMContentLoaded', function() {
    // State variables
    let currentPage = 1;
    let perPage = 50;
    let totalFiles = 0;
    let totalPages = 0;
    
    // DOM elements
    const responseArea = document.getElementById('response');
    const filesTableBody = document.getElementById('filesTableBody');
    const totalFilesElement = document.getElementById('totalFiles');
    const currentPageElement = document.getElementById('currentPage');
    const perPageElement = document.getElementById('perPage');
    const totalPagesElement = document.getElementById('totalPages');
    const pageInfoElement = document.getElementById('pageInfo');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const pageInput = document.getElementById('pageInput');
    const perPageSelect = document.getElementById('perPageSelect');
    const refreshBtn = document.getElementById('refreshBtn');
    const exportBtn = document.getElementById('exportBtn');
    const goToPageBtn = document.getElementById('goToPage');
    const clearResponseBtn = document.getElementById('clearResponse');
    const exportResponseBtn = document.getElementById('exportResponse');
    
    // Load initial data
    loadGoogleDriveFiles();
    
    // Event listeners
    refreshBtn.addEventListener('click', loadGoogleDriveFiles);
    exportBtn.addEventListener('click', exportToCSV);
    prevPageBtn.addEventListener('click', () => changePage(currentPage - 1));
    nextPageBtn.addEventListener('click', () => changePage(currentPage + 1));
    goToPageBtn.addEventListener('click', goToPage);
    clearResponseBtn.addEventListener('click', clearResponse);
    exportResponseBtn.addEventListener('click', exportResponse);
    
    perPageSelect.addEventListener('change', function() {
        perPage = parseInt(this.value);
        currentPage = 1;
        loadGoogleDriveFiles();
    });
    
    pageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            goToPage();
        }
    });
    
    async function loadGoogleDriveFiles() {
        try {
            responseArea.textContent = 'Loading Google Drive files...';
            
            const response = await fetch(`/api/google-drive-files?page=${currentPage}&per_page=${perPage}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                updateStatistics(data);
                renderTable(data.files);
                updatePagination(data);
                responseArea.textContent = JSON.stringify(data, null, 2);
            } else {
                responseArea.textContent = `Error: ${data.message}`;
                filesTableBody.innerHTML = '<tr><td colspan="7" class="loading">Error loading files</td></tr>';
            }
        } catch (error) {
            responseArea.textContent = `Error: ${error.message}`;
            filesTableBody.innerHTML = '<tr><td colspan="7" class="loading">Error loading files</td></tr>';
        }
    }
    
    function updateStatistics(data) {
        totalFiles = data.total_count;
        totalPages = data.pages;
        
        totalFilesElement.textContent = totalFiles.toLocaleString();
        currentPageElement.textContent = currentPage;
        perPageElement.textContent = perPage;
        totalPagesElement.textContent = totalPages;
    }
    
    function renderTable(files) {
        if (files.length === 0) {
            filesTableBody.innerHTML = '<tr><td colspan="8" class="loading">No files found</td></tr>';
            return;
        }
        
        const rows = files.map(file => `
            <tr>
                <td class="file-id">${file.id}</td>
                <td class="file-id">${file.quip_document_id || 'N/A'}</td>
                <td class="file-id">${file.google_drive_file_id || 'N/A'}</td>
                <td class="file-name" title="${file.google_drive_file_name || 'N/A'}">${file.google_drive_file_name || 'N/A'}</td>
                <td class="file-url" title="${file.google_drive_file_url || 'N/A'}">${file.google_drive_file_url || 'N/A'}</td>
                <td>${file.when_quip_created ? new Date(file.when_quip_created).toLocaleString() : 'N/A'}</td>
                <td>${file.document_type || 'N/A'}</td>
                <td>
                    ${file.google_drive_file_url ? `<a href="${file.google_drive_file_url}" target="_blank" class="btn btn-primary btn-sm me-1"><i class="bi bi-eye"></i> View</a>` : ''}
                    <button onclick="copyToClipboard('${file.google_drive_file_id || ''}', this)" class="btn btn-success btn-sm">
                        <i class="bi bi-clipboard"></i> Copy ID
                    </button>
                </td>
            </tr>
        `).join('');
        
        filesTableBody.innerHTML = rows;
    }
    
    function updatePagination(data) {
        // Update page info
        pageInfoElement.textContent = `Page ${data.page} of ${data.pages}`;
        
        // Update navigation buttons
        prevPageBtn.disabled = !data.has_prev;
        nextPageBtn.disabled = !data.has_next;
        
        // Update page input
        pageInput.value = currentPage;
        pageInput.max = totalPages;
    }
    
    function changePage(newPage) {
        if (newPage >= 1 && newPage <= totalPages) {
            currentPage = newPage;
            loadGoogleDriveFiles();
        }
    }
    
    function goToPage() {
        const page = parseInt(pageInput.value);
        if (page >= 1 && page <= totalPages) {
            currentPage = page;
            loadGoogleDriveFiles();
        } else {
            alert(`Please enter a valid page number between 1 and ${totalPages}`);
        }
    }
    
    function clearResponse() {
        responseArea.textContent = 'Ready to load Google Drive files...';
    }
    
    function exportResponse() {
        const content = responseArea.textContent;
        if (content && content !== 'Ready to load Google Drive files...') {
            try {
                const blob = new Blob([content], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'google-drive-files-response.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Export failed:', error);
            }
        }
    }
    
    async function exportToCSV() {
        try {
            // Get all files (not just current page)
            const response = await fetch(`/api/google-drive-files?page=1&per_page=${totalFiles}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                const csvContent = generateCSV(data.files);
                downloadCSV(csvContent, 'google-drive-files.csv');
            } else {
                alert('Error exporting data: ' + data.message);
            }
        } catch (error) {
            alert('Error exporting data: ' + error.message);
        }
    }
    
    function generateCSV(files) {
        const headers = [
            'ID',
            'Quip Document ID', 
            'Google Drive File ID',
            'File Name',
            'File URL',
            'Created At',
            'Document Type',
            'Author',
            'Migration Completed'
        ];
        
        const rows = files.map(file => [
            file.id,
            file.quip_document_id || '',
            file.google_drive_file_id || '',
            file.google_drive_file_name || '',
            file.google_drive_file_url || '',
            file.when_quip_created ? new Date(file.when_quip_created).toLocaleString() : '',
            file.document_type || '',
            file.author || '',
            file.when_migration_completed ? new Date(file.when_migration_completed).toLocaleString() : ''
        ]);
        
        return [headers, ...rows]
            .map(row => row.map(cell => `"${cell}"`).join(','))
            .join('\n');
    }
    
    function downloadCSV(content, filename) {
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    // Global function for copying to clipboard
    window.copyToClipboard = function(text, buttonElement) {
        if (!text) {
            alert('No text to copy');
            return;
        }
        
        // If buttonElement is not provided, try to get it from the event
        if (!buttonElement && event && event.target) {
            buttonElement = event.target;
        }
        
        // Store original button content
        const originalHTML = buttonElement ? buttonElement.innerHTML : '';
        const originalClasses = buttonElement ? buttonElement.className : '';
        
        // Try modern clipboard API first
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                // Show success message
                if (buttonElement) {
                    buttonElement.innerHTML = '<i class="bi bi-check"></i> Copied!';
                    buttonElement.classList.remove('btn-success');
                    buttonElement.classList.add('btn-success');
                    
                    setTimeout(() => {
                        buttonElement.innerHTML = originalHTML;
                        buttonElement.className = originalClasses;
                    }, 1000);
                } else {
                    alert('Copied to clipboard: ' + text);
                }
            }).catch(err => {
                console.error('Clipboard API failed:', err);
                // Fallback to older method
                fallbackCopyToClipboard(text, buttonElement, originalHTML, originalClasses);
            });
        } else {
            // Fallback for older browsers
            fallbackCopyToClipboard(text, buttonElement, originalHTML, originalClasses);
        }
    };
    
    // Fallback clipboard method for older browsers
    function fallbackCopyToClipboard(text, buttonElement, originalHTML, originalClasses) {
        try {
            // Create a temporary textarea element
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            
            if (successful) {
                // Show success message
                if (buttonElement) {
                    buttonElement.innerHTML = '<i class="bi bi-check"></i> Copied!';
                    buttonElement.classList.remove('btn-success');
                    buttonElement.classList.add('btn-success');
                    
                    setTimeout(() => {
                        buttonElement.innerHTML = originalHTML;
                        buttonElement.className = originalClasses;
                    }, 1000);
                } else {
                    alert('Copied to clipboard: ' + text);
                }
            } else {
                throw new Error('execCommand copy failed');
            }
        } catch (err) {
            console.error('Fallback copy failed:', err);
            // Show the text to copy manually
            const manualCopyText = 'Please copy this text manually: ' + text;
            if (buttonElement) {
                buttonElement.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Manual Copy';
                buttonElement.classList.remove('btn-success');
                buttonElement.classList.add('btn-warning');
                buttonElement.title = manualCopyText;
                
                setTimeout(() => {
                    buttonElement.innerHTML = originalHTML;
                    buttonElement.className = originalClasses;
                    buttonElement.title = '';
                }, 2000);
            } else {
                alert(manualCopyText);
            }
        }
    }
}); 