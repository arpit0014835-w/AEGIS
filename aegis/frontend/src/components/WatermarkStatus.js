'use client'; 

export default function WatermarkStatus({ watermarks = [] }) { 
    const verified = watermarks.filter((w) => w.verified).length;	
    const total = watermarks.length;	

    return ( 
        <div className="card"> 
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">	
                <p className="text-sm font-semibold text-text-primary">Watermark Verification</p>	
                {total > 0 && ( 
                    <span className={`badge ${verified === total ? 'badge-success' : 'badge-warning'}`}> 
                        {verified}/{total} verified	
                    </span>	
                )}	
            </div> 

            {watermarks.length === 0 ? ( 
                <div className="px-6 py-8 text-center text-sm text-text-secondary"> 
                    No watermark data available. 
                </div> 
            ) : (	
                <ul className="divide-y divide-border">	
                    {watermarks.map((w, i) => { 
                        const filename = w.file_path || w.file || `File ${i + 1}`; 
                        const short = filename.split('/').pop();	
                        return (	
                            <li key={i} className="px-6 py-3 flex items-center justify-between gap-4"> 
                                <div className="min-w-0"> 
                                    <p	
                                        className="text-sm text-text-primary truncate font-mono"	
                                        title={filename}	
                                    > 
                                        {short} 
                                    </p>	
                                    {w.author && ( 
                                        <p className="text-xs text-text-secondary mt-0.5">{w.author}</p>	
                                    )}	
                                </div> 
                                <span 
                                    className={`badge shrink-0 ${w.verified ? 'badge-success' : 'badge-danger'	
                                        }`} 
                                >	
                                    {w.verified ? 'Verified' : 'Unverified'} 
                                </span>	
                            </li>	
                        ); 
                    })} 
                </ul>	
            )} 
        </div> 
    ); 
}	
