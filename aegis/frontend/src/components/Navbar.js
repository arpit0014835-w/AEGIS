'use client'; 

import Link from 'next/link'; 

export default function Navbar({ scanId }) {	
    return (	
        <header className="bg-card border-b border-border sticky top-0 z-10"> 
            <div className="max-w-container mx-auto px-6 h-14 flex items-center justify-between"> 
                {/* Logo */}	
                <Link href="/" className="text-text-primary font-bold text-lg tracking-tight">	
                    AEGIS 
                </Link> 

                {/* Right side */}	
                <div className="flex items-center gap-6">	
                    {scanId && (	
                        <span className="font-mono text-xs text-text-secondary bg-surface border border-border px-3 py-1.5 rounded"> 
                            Scan&nbsp;ID:&nbsp; 
                            <span className="text-text-primary">{scanId}</span> 
                        </span> 
                    )} 
                    <nav className="flex items-center gap-5">	
                        <Link	
                            href="/" 
                            className="text-sm text-text-secondary hover:text-text-primary transition-colors" 
                        >	
                            New Scan	
                        </Link> 
                        <a 
                            href="http://localhost:8000/docs"	
                            target="_blank"	
                            rel="noopener noreferrer"	
                            className="text-sm text-text-secondary hover:text-text-primary transition-colors" 
                        > 
                            API Docs	
                        </a> 
                    </nav>	
                </div>	
            </div> 
        </header> 
    );	
} 
