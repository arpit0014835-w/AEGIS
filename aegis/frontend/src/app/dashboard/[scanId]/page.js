'use client'; 

import { useEffect } from 'react'; 
import { useParams } from 'next/navigation';	
import Navbar from '@/components/Navbar';	
import TrustScoreCard from '@/components/TrustScoreCard'; 
import StatCard from '@/components/StatCard'; 
import VulnerabilitySummary from '@/components/VulnerabilitySummary';	
import VulnerabilityTable from '@/components/VulnerabilityTable';	
import FileHeatmap from '@/components/FileHeatmap'; 
import WatermarkStatus from '@/components/WatermarkStatus'; 
import ScanProgress from '@/components/ScanProgress';	
import { useScanStatus } from '@/hooks/useScanStatus';	

export default function DashboardPage() {	
    const params = useParams(); 
    const scanId = params.scanId; 
    const { status, report, error, isPolling, startPolling } = useScanStatus(scanId); 

    useEffect(() => { 
        if (scanId) startPolling(); 
    }, [scanId, startPolling]);	

    const isComplete = status?.status === 'completed' && report;	
    const isFailed = status?.status === 'failed' || !!error; 

    // ----------- Derived data from report ----------- 
    const trustScore = report?.trust_score ?? 0;	
    const vulnerabilities = report?.breach_secure?.vulnerabilities ?? [];	
    const totalVulns = vulnerabilities.length; 
    const criticalCount = vulnerabilities.filter((v) => v.severity === 'critical').length; 
    const highCount = vulnerabilities.filter((v) => v.severity === 'high').length;	
    const mediumCount = vulnerabilities.filter((v) => v.severity === 'medium').length;	
    const fileAnalyses = report?.ghost_detect?.file_analyses ?? [];	
    const aiPercent = report?.ghost_detect?.ai_percentage ?? null; 
    const watermarks = report?.proof_vary?.watermarks ?? report?.proof_verify?.watermarks ?? []; 
    const breakdown = report?.breakdown ?? {};	

    return ( 
        <>	
            <Navbar scanId={scanId} />	

            <div className="max-w-container mx-auto px-6 py-8"> 

                {/* Page heading */} 
                <div className="mb-8">	
                    <h1 className="text-xl font-bold text-text-primary"> 
                        {isComplete ? 'Analysis Report' : isFailed ? 'Scan Failed' : 'Analysis in Progress'}	
                    </h1> 
                    {report?.repo_url && (	
                        <p className="text-sm text-text-secondary mt-1 font-mono">{report.repo_url}</p>	
                    )} 
                </div> 

                {/* Error state */}	
                {isFailed && ( 
                    <div 
                        id="scan-error" 
                        className="mb-6 px-5 py-4 rounded-md border border-danger/20 bg-danger-light text-sm text-danger"	
                    >	
                        {error || status?.error || 'The scan failed. Please try again.'} 
                    </div> 
                )}	

                {/* In-progress state */} 
                {!isComplete && !isFailed && (	
                    <div className="max-w-md mx-auto mt-12"> 
                        <ScanProgress status={status} /> 
                    </div>	
                )}	

                {/* Results */} 
                {isComplete && (	
                    <div className="space-y-6">	

                        {/* Row 1: KPI cards */} 
                        <div className="grid grid-cols-3 gap-4">
                            <TrustScoreCard score={trustScore} />

                            <StatCard
                                label="Vulnerabilities Found"
                                value={totalVulns}
                                colorClass={totalVulns > 0 ? 'text-danger' : 'text-success'}
                                subtext={
                                    totalVulns > 0
                                        ? `${criticalCount} Critical  ${highCount} High  ${mediumCount} Medium`
                                        : 'No vulnerabilities detected'
                                }
                            />

                            <StatCard
                                label="AI-Generated Code"
                                value={aiPercent !== null ? `${Math.round(aiPercent)}%` : '—'}
                                colorClass={
                                    aiPercent === null ? 'text-text-primary' :
                                        aiPercent > 60 ? 'text-danger' :
                                            aiPercent > 30 ? 'text-warning' : 'text-success'
                                }
                                subtext="of files flagged by Ghost Detect"
                            />
                        </div>

                        {/* Row 2: Score breakdown */}
                        {(breakdown.ghost_detect_score != null || breakdown.breach_secure_score != null) && (
                            <div className="card p-6">
                                <p className="section-heading">Score Breakdown</p>
                                <div className="grid grid-cols-3 gap-6">
                                    {[
                                        { label: 'Ghost Detect', weight: '35%', score: breakdown.ghost_detect_score },
                                        { label: 'Breach Secure', weight: '40%', score: breakdown.breach_secure_score },
                                        { label: 'Proof Verify', weight: '25%', score: breakdown.proof_verify_score },
                                    ].map((b) => {
                                        const s = Math.round(b.score ?? 0);
                                        const color =
                                            s >= 70 ? '#16A34A' :
                                                s >= 40 ? '#D97706' : '#DC2626';
                                        return (
                                            <div key={b.label}>
                                                <div className="flex items-center justify-between mb-1.5">
                                                    <span className="text-sm text-text-primary font-medium">{b.label}</span>
                                                    <span className="text-xs text-text-secondary">{b.weight}</span>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full rounded-full"
                                                            style={{ width: `${s}%`, backgroundColor: color }}
                                                        />
                                                    </div>
                                                    <span className="text-sm font-semibold tabular-nums" style={{ color }}>
                                                        {s}
                                                    </span>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Row 3: Vulnerability summary + Watermarks */}
                        <div className="grid grid-cols-[3fr_2fr] gap-4">
                            <VulnerabilitySummary
                                vulnerabilities={vulnerabilities}
                                totalCount={totalVulns}
                            />
                            <WatermarkStatus watermarks={watermarks} />
                        </div>

                        {/* Row 4: Heatmap */}
                        <FileHeatmap files={fileAnalyses} />

                        {/* Row 5: Full vulnerability table */}
                        {vulnerabilities.length > 0 && (
                            <VulnerabilityTable vulnerabilities={vulnerabilities} />
                        )}

                        {/* Row 6: Scan metadata footer */}
                        <div className="card px-6 py-4 flex items-center justify-between text-xs text-text-secondary">
                            <span>
                                {report.total_files_analyzed != null && (
                                    <>{report.total_files_analyzed} files analyzed</>
                                )}
                                {report.languages_detected?.length > 0 && (
                                    <>&nbsp;&middot;&nbsp;{report.languages_detected.join(', ')}</>
                                )}
                            </span>
                            <span className="font-mono">{scanId}</span>
                        </div>

                    </div>
                )}
            </div>
        </>
    );
}
