'use client'; 

function getTrustColor(score) { 
    if (score >= 70) return { bar: '#16A34A', text: 'text-success' };	
    if (score >= 40) return { bar: '#D97706', text: 'text-warning' };	
    return { bar: '#DC2626', text: 'text-danger' }; 
} 

function getTrustLabel(score) {	
    if (score >= 70) return 'Good';	
    if (score >= 40) return 'Needs Attention'; 
    return 'High Risk'; 
}	

export default function TrustScoreCard({ score }) {	
    const numericScore = Math.round(score ?? 0);	
    const { bar: barColor, text: textColor } = getTrustColor(numericScore); 

    return ( 
        <div className="card p-6"> 
            <p className="section-heading">Trust Score</p> 
            <div className="flex items-end gap-1 mb-4"> 
                <span className={`text-5xl font-bold tabular-nums leading-none ${textColor}`}>	
                    {numericScore}	
                </span> 
                <span className="text-xl text-text-secondary font-medium mb-1">/100</span> 
            </div>	

            {/* Progress bar */}	
            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden mb-3"> 
                <div 
                    className="h-full rounded-full transition-all duration-500"	
                    style={{ width: `${numericScore}%`, backgroundColor: barColor }}	
                />	
            </div> 

            <div className="flex items-center justify-between"> 
                <span className="text-xs text-text-secondary">Codebase Trust Score</span>	
                <span 
                    className="text-xs font-semibold"	
                    style={{ color: barColor }}	
                > 
                    {getTrustLabel(numericScore)} 
                </span>	
            </div> 
        </div>	
    ); 
}	
