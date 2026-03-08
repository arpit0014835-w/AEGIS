'use client'; 

import { useState } from 'react'; 

function getCellStyle(probability) {	
    // Scale from light gray to a blue tint	
    const p = Math.min(1, Math.max(0, probability || 0)); 
    const r = Math.round(241 - p * 60); 
    const g = Math.round(245 - p * 80);	
    const b = Math.round(249 + p * 6);	
    return { backgroundColor: `rgb(${r},${g},${b})` }; 
} 

export default function FileHeatmap({ files = [] }) {	
    const [tooltip, setTooltip] = useState(null);	

    if (!files.length) {	
        return ( 
            <div className="card p-6"> 
                <p className="section-heading">File-Level AI Probability</p> 
                <p className="text-sm text-text-secondary">No file data available.</p> 
            </div> 
        );	
    }	

    return ( 
        <div className="card p-6"> 
            <div className="mb-4">	
                <p className="text-sm font-semibold text-text-primary mb-0.5">File-Level AI Probability</p>	
                <p className="text-xs text-text-secondary"> 
                    Each cell represents one file. Darker cells indicate higher estimated AI-generation probability. 
                    Hover for details.	
                </p>	
            </div>	

            <div className="relative"> 
                <div className="flex flex-wrap gap-1"> 
                    {files.map((file, i) => (	
                        <div 
                            key={i}	
                            className="w-8 h-8 rounded cursor-default border border-border/60 transition-transform hover:scale-110"	
                            style={getCellStyle(file.ai_probability)} 
                            onMouseEnter={(e) => { 
                                const rect = e.currentTarget.getBoundingClientRect();	
                                setTooltip({ 
                                    x: rect.left,	
                                    y: rect.bottom + 6, 
                                    name: file.path || file.name || `File ${i + 1}`,	
                                    prob: ((file.ai_probability || 0) * 100).toFixed(0),	
                                }); 
                            }} 
                            onMouseLeave={() => setTooltip(null)}	
                        /> 
                    ))} 
                </div> 

                {tooltip && (	
                    <div	
                        className="fixed z-50 bg-text-primary text-white text-xs rounded px-3 py-2 pointer-events-none shadow-lg" 
                        style={{ left: tooltip.x, top: tooltip.y }} 
                    >	
                        <p className="font-medium truncate max-w-xs">{tooltip.name}</p> 
                        <p className="text-white/70 mt-0.5">AI probability: {tooltip.prob}%</p>	
                    </div> 
                )} 
            </div>	

            {/* Legend */}	
            <div className="flex items-center gap-2 mt-4"> 
                <span className="text-xs text-text-secondary">Low</span>	
                <div className="flex gap-0.5">	
                    {[0, 0.25, 0.5, 0.75, 1].map((p) => ( 
                        <div
                            key={p}
                            className="w-5 h-3 rounded-sm border border-border/50"
                            style={getCellStyle(p)}
                        />
                    ))}
                </div>
                <span className="text-xs text-text-secondary">High</span>
            </div>
        </div>
    );
}
