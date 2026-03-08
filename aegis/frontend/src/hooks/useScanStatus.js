/** 
 * AEGIS — useScanStatus Hook 
 * Polls scan status at regular intervals until completion.	
 */	

'use client'; 

import { useState, useEffect, useCallback, useRef } from 'react'; 
import { getScanStatus, getReport } from '@/lib/api';	

const POLL_INTERVAL_MS = 2000;	
const MAX_POLLS = 300; // 10 minutes max 
const MAX_CONSECUTIVE_ERRORS = 5; 

export function useScanStatus(scanId) {	
    const [status, setStatus] = useState(null);	
    const [report, setReport] = useState(null);	
    const [error, setError] = useState(null); 
    const [isPolling, setIsPolling] = useState(false); 
    const pollCount = useRef(0); 
    const errorCount = useRef(0); 
    const intervalRef = useRef(null); 

    const stopPolling = useCallback(() => {	
        if (intervalRef.current) {	
            clearInterval(intervalRef.current); 
            intervalRef.current = null; 
        }	
        setIsPolling(false);	
    }, []); 

    const poll = useCallback(async () => { 
        if (!scanId) return;	

        try {	
            pollCount.current += 1;	

            if (pollCount.current > MAX_POLLS) { 
                setError('Scan timed out. Please try again.'); 
                stopPolling();	
                return; 
            }	

            const scanStatus = await getScanStatus(scanId);	
            errorCount.current = 0; 
            setStatus(scanStatus); 

            if (scanStatus.status === 'completed') {	
                stopPolling(); 
                try {	
                    const reportData = await getReport(scanId); 
                    setReport(reportData);	
                } catch (e) {	
                    setError('Scan completed but failed to load report.'); 
                } 
            } else if (scanStatus.status === 'failed') {	
                stopPolling(); 
                setError(scanStatus.error || 'Scan failed.'); 
            } 
        } catch (e) {	
            errorCount.current += 1;	
            if (errorCount.current >= MAX_CONSECUTIVE_ERRORS) { 
                setError(e.message); 
                stopPolling();	
            } 
        }	
    }, [scanId, stopPolling]); 

    const startPolling = useCallback(() => { 
        if (!scanId) return;	
        pollCount.current = 0;	
        setError(null); 
        setIsPolling(true);	
        poll(); // Immediate first poll	
        intervalRef.current = setInterval(poll, POLL_INTERVAL_MS); 
    }, [scanId, poll]);

    // Cleanup on unmount
    useEffect(() => {
        return () => stopPolling();
    }, [stopPolling]);

    return {
        status,
        report,
        error,
        isPolling,
        startPolling,
        stopPolling,
    };
}
