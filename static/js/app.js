document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const searchResults = document.getElementById('searchResults');
    const quipDocumentInfo = document.getElementById('quipDocumentInfo');
    const googleDriveInfo = document.getElementById('googleDriveInfo');
    
    // Function to extract Google Drive document ID from URL
    function extractGoogleDriveId(input) {
        // Check if it's a Google Doc URL
        const googleDocPattern = /docs\.google\.com\/document\/d\/([a-zA-Z0-9_-]+)/;
        const googleSheetPattern = /docs\.google\.com\/spreadsheets\/d\/([a-zA-Z0-9_-]+)/;
        const googleSlidePattern = /docs\.google\.com\/presentation\/d\/([a-zA-Z0-9_-]+)/;
        
        let match = input.match(googleDocPattern) || 
                   input.match(googleSheetPattern) || 
                   input.match(googleSlidePattern);
        
        if (match) {
            return {
                type: 'google',
                id: match[1],
                originalInput: input
            };
        }
        
        // Check if it looks like a Google Drive ID (long alphanumeric string)
        const googleIdPattern = /^[a-zA-Z0-9_-]{25,}$/;
        if (googleIdPattern.test(input)) {
            return {
                type: 'google',
                id: input,
                originalInput: input
            };
        }
        
        // Assume it's a Quip document ID
        return {
            type: 'quip',
            id: input,
            originalInput: input
        };
    }
    
    // Search functionality
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    async function performSearch() {
        const input = searchInput.value.trim();
        
        if (!input) {
            alert('Please enter a Quip Document ID or paste a Google Doc URL to search');
            return;
        }
        
        // Extract the document ID and determine search type
        const searchInfo = extractGoogleDriveId(input);
        
        // Show user feedback about what we're searching for
        let searchMessage = '';
        if (searchInfo.type === 'google') {
            if (searchInfo.originalInput !== searchInfo.id) {
                searchMessage = `Extracted Google Drive ID: ${searchInfo.id} from URL`;
            } else {
                searchMessage = `Searching for Google Drive ID: ${searchInfo.id}`;
            }
        } else {
            searchMessage = `Searching for Quip Document ID: ${searchInfo.id}`;
        }
        
        // Update button text to show what we're doing
        searchBtn.textContent = 'Searching...';
        searchBtn.disabled = true;
        
        try {
            const response = await fetch(`/api/search?document_id=${encodeURIComponent(searchInfo.id)}&search_type=${searchInfo.type}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                // Display results in the search results section
                displaySearchResults(data);
            } else {
                // Show error in search results
                displaySearchError(data.message);
            }
        } catch (error) {
            displaySearchError(`Error: ${error.message}`);
        } finally {
            searchBtn.textContent = 'Search';
            searchBtn.disabled = false;
        }
    }
    
    function displaySearchResults(data) {
        searchResults.style.display = 'block';
        
        // Store the document ID for restoration
        if (data.search_type === 'quip') {
            currentDocumentId = data.quip_document.quip_id;
        } else {
            currentDocumentId = data.google_drive_file.google_drive_file_id;
        }
        
        // Enable restore buttons
        document.getElementById('restoreDocx').disabled = false;
        document.getElementById('restorePdf').disabled = false;
        document.getElementById('restoreHtml').disabled = false;
        
        // Clear restore status
        document.getElementById('restoreStatus').style.display = 'none';
        
        if (data.search_type === 'quip') {
            // Display Quip document info first (since we searched by Quip ID)
            const quipDoc = data.quip_document;
            quipDocumentInfo.textContent = `Document Type: ${data.document_type}
Quip ID: ${quipDoc.quip_id}
Name: ${quipDoc.obfuscated_name || 'N/A'}
Google Drive ID: ${quipDoc.google_drive_id || 'N/A'}
Document Type: ${quipDoc.document_type || 'N/A'}
Author: ${quipDoc.author || 'N/A'}
Created: ${quipDoc.when_quip_created || 'N/A'}
Migration Completed: ${quipDoc.when_migration_completed || 'N/A'}`;
            
            // Display Google Drive file info
            const gdriveFile = data.google_drive_file;
            if (gdriveFile) {
                googleDriveInfo.textContent = `File ID: ${gdriveFile.google_drive_file_id}
File Name: ${gdriveFile.google_drive_file_name || 'N/A'}
File URL: ${gdriveFile.google_drive_file_url || 'N/A'}
Created: ${gdriveFile.created_at || 'N/A'}`;
            } else {
                googleDriveInfo.textContent = 'No corresponding Google Drive file found for this Quip document.';
            }
        } else {
            // Display Google Drive file info first (since we searched by Google Drive ID)
            const gdriveFile = data.google_drive_file;
            googleDriveInfo.textContent = `File ID: ${gdriveFile.google_drive_file_id}
File Name: ${gdriveFile.google_drive_file_name || 'N/A'}
File URL: ${gdriveFile.google_drive_file_url || 'N/A'}
Created: ${gdriveFile.created_at || 'N/A'}`;
            
            // Display Quip document info
            const quipDoc = data.quip_document;
            if (quipDoc) {
                if (data.document_type === 'file') {
                    quipDocumentInfo.textContent = `Document Type: ${data.document_type}
Quip ID: ${quipDoc.quip_id}
Name: ${quipDoc.obfuscated_name || 'N/A'}
Google Drive ID: ${quipDoc.google_drive_id || 'N/A'}
Document Type: ${quipDoc.document_type || 'N/A'}
Author: ${quipDoc.author || 'N/A'}
Created: ${quipDoc.when_quip_created || 'N/A'}
Migration Completed: ${quipDoc.when_migration_completed || 'N/A'}`;
                } else {
                    quipDocumentInfo.textContent = `Document Type: ${data.document_type}
Quip ID: ${quipDoc.quip_id}
Name: ${quipDoc.obfuscated_name || 'N/A'}
Google Drive ID: ${quipDoc.google_drive_id || 'N/A'}
Parent Folder: ${quipDoc.parent_folder || 'N/A'}
Inherit Mode: ${quipDoc.inherit_mode || 'N/A'}
Member Count: ${quipDoc.member_count || 'N/A'}`;
                }
            } else {
                quipDocumentInfo.textContent = 'No corresponding Quip document found for this Google Drive file.';
            }
        }
    }
    
    function displaySearchError(message) {
        searchResults.style.display = 'block';
        quipDocumentInfo.textContent = `Error: ${message}`;
        googleDriveInfo.textContent = 'No data available due to error.';
        
        // Disable restore buttons on error
        currentDocumentId = null;
        document.getElementById('restoreDocx').disabled = true;
        document.getElementById('restorePdf').disabled = true;
        document.getElementById('restoreHtml').disabled = true;
        document.getElementById('restoreStatus').style.display = 'none';
    }
    
    // Quick stats button
    document.getElementById('quickStats').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.status === 'success') {
                const stats = data.statistics.documents;
                alert(`Migration Statistics:\n\nTotal Documents: ${stats.total}\nMigrated: ${stats.migrated}\nPending: ${stats.pending}\nFailed: ${stats.failed || 0}`);
            } else {
                alert('Failed to load statistics');
            }
        } catch (error) {
            alert(`Error loading statistics: ${error.message}`);
        }
    });
    
    // Restore functionality
    let currentDocumentId = null;
    
    document.getElementById('restoreDocx').addEventListener('click', function() {
        restoreDocument('docx');
    });
    
    document.getElementById('restorePdf').addEventListener('click', function() {
        restoreDocument('pdf');
    });
    
    document.getElementById('restoreHtml').addEventListener('click', function() {
        restoreDocument('html');
    });
    
    async function restoreDocument(format) {
        if (!currentDocumentId) {
            alert('No document selected for restoration');
            return;
        }
        
        const restoreStatus = document.getElementById('restoreStatus');
        const buttons = [document.getElementById('restoreDocx'), document.getElementById('restorePdf'), document.getElementById('restoreHtml')];
        
        // Disable all buttons and show status
        buttons.forEach(btn => btn.disabled = true);
        restoreStatus.style.display = 'block';
        restoreStatus.innerHTML = `<div class="alert alert-info"><i class="bi bi-hourglass-split"></i> Converting document to ${format.toUpperCase()}...</div>`;
        
        try {
            const response = await fetch('/api/restore-file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    document_id: currentDocumentId,
                    format: format
                })
            });
            
            if (response.ok) {
                if (format === 'html') {
                    // For HTML, we get JSON response with content
                    const data = await response.json();
                    if (data.status === 'success') {
                        // Create and download HTML file
                        const blob = new Blob([data.content], { type: 'text/html' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = data.filename;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        
                        restoreStatus.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> Document restored successfully as ${data.filename}</div>`;
                    } else {
                        throw new Error(data.message);
                    }
                } else {
                    // For DOCX/PDF, we get file download
                    const blob = await response.blob();
                    const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || `document.${format}`;
                    
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    restoreStatus.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> Document restored successfully as ${filename}</div>`;
                }
            } else {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to restore document');
            }
        } catch (error) {
            restoreStatus.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle"></i> Error: ${error.message}</div>`;
        } finally {
            // Re-enable buttons
            buttons.forEach(btn => btn.disabled = false);
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
}); 