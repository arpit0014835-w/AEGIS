/** 
 * AEGIS — API Client 
 * Centralised API communication layer.	
 */	

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'; 

/** 
 * Generic fetch wrapper with error handling.	
 */	
async function apiFetch(endpoint, options = {}) { 
    const url = `${API_BASE}${endpoint}`; 
    const config = {	
        headers: {	
            'Content-Type': 'application/json',	
            ...options.headers, 
        }, 
        ...options, 
    }; 

    const response = await fetch(url, config); 

    if (!response.ok) {	
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));	
        throw new Error(error.detail || `API error: ${response.status}`); 
    } 

    return response.json();	
}	

/** 
 * Submit a GitHub repository for scanning. 
 * @param {string} repoUrl - GitHub repository URL	
 * @returns {Promise<object>} Scan status response	
 */	
export async function submitScan(repoUrl) { 
    return apiFetch('/scans', { 
        method: 'POST',	
        body: JSON.stringify({ repo_url: repoUrl }), 
    });	
}	

/** 
 * Upload a ZIP file for scanning. 
 * @param {File} file - ZIP file to upload	
 * @returns {Promise<object>} Scan status response 
 */	
export async function uploadScan(file) { 
    const formData = new FormData();	
    formData.append('file', file);	

    const url = `${API_BASE}/scans/upload`; 
    const response = await fetch(url, { 
        method: 'POST',	
        body: formData, 
    }); 

    if (!response.ok) { 
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));	
        throw new Error(error.detail || `Upload error: ${response.status}`);	
    } 

    return response.json(); 
}	

/** 
 * Get scan status.	
 * @param {string} scanId - UUID of the scan 
 * @returns {Promise<object>} Current scan status 
 */	
export async function getScanStatus(scanId) {	
    return apiFetch(`/scans/${scanId}`); 
}	

/**	
 * Get the full analysis report. 
 * @param {string} scanId - UUID of the scan
 * @returns {Promise<object>} Trust Score report
 */
export async function getReport(scanId) {
    return apiFetch(`/reports/${scanId}`);
}

/**
 * Health check.
 * @returns {Promise<object>} Service health status
 */
export async function healthCheck() {
    return apiFetch('/health');
}
