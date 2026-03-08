'use client'; 

export default function StatCard({ label, value, subtext, colorClass = 'text-text-primary' }) { 
    return (	
        <div className="card p-6">	
            <p className="section-heading">{label}</p> 
            <p className={`text-5xl font-bold tabular-nums leading-none mb-2 ${colorClass}`}> 
                {value ?? '—'}	
            </p>	
            {subtext && ( 
                <p className="text-xs text-text-secondary">{subtext}</p> 
            )}	
        </div>	
    );	
} 
