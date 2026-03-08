'use client'; 

import { useEffect, useRef } from 'react'; 

const STEPS = [	
    { key: 'queued', label: 'Queued' },	
    { key: 'ingesting', label: 'Ingesting Repository' }, 
    { key: 'analyzing', label: 'Running Analysis' }, 
    { key: 'scoring', label: 'Computing Trust Score' },	
    { key: 'completed', label: 'Complete' },	
]; 

// Map backend stage values to our simplified step keys 
const STAGE_MAP = {	
    queued: 'queued',	
    cloning: 'ingesting',	
    parsing: 'ingesting', 
    ghost_detect: 'analyzing', 
    breach_secure: 'analyzing', 
    proof_verify: 'analyzing', 
    scoring: 'scoring', 
    completed: 'completed',	
    failed: 'completed',	
}; 

function getStepIndex(status) { 
    const mapped = STAGE_MAP[status] || status;	
    const idx = STEPS.findIndex((s) => s.key === mapped);	
    return idx === -1 ? 0 : idx; 
} 

export default function ScanProgress({ status }) {	
    const currentStep = status?.current_stage || status?.status || 'queued';	
    const currentIdx = getStepIndex(currentStep);	

    return ( 
        <div className="card p-6"> 
            <p className="text-sm font-semibold text-text-primary mb-6">Analysis in Progress</p>	

            <ol className="space-y-4"> 
                {STEPS.map((step, i) => {	
                    const done = i < currentIdx;	
                    const active = i === currentIdx; 
                    const pending = i > currentIdx; 

                    return (	
                        <li key={step.key} className="flex items-center gap-4"> 
                            {/* Step indicator */}	
                            <div 
                                className={`	
                                    w-7 h-7 rounded-full border-2 flex items-center justify-center shrink-0 text-xs font-semibold	
                                    ${done ? 'bg-success border-success text-white' : ''} 
                                    ${active ? 'border-primary bg-primary-light text-primary' : ''} 
                                    ${pending ? 'border-border bg-white text-text-secondary' : ''}	
                                `} 
                            > 
                                {done ? ( 
                                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">	
                                        <path d="M2 6l3 3 5-5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />	
                                    </svg> 
                                ) : ( 
                                    i + 1	
                                )} 
                            </div>	

                            {/* Label */} 
                            <span 
                                className={`text-sm ${done ? 'text-text-secondary' :	
                                        active ? 'text-text-primary font-medium' :	
                                            'text-text-secondary' 
                                    }`}	
                            >	
                                {step.label} 
                                {active && (
                                    <span className="ml-2 text-xs text-primary font-normal">Running...</span>
                                )}
                            </span>
                        </li>
                    );
                })}
            </ol>

            {status?.message && (
                <p className="mt-5 text-xs text-text-secondary border-t border-border pt-4">
                    {status.message}
                </p>
            )}
        </div>
    );
}
