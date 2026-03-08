import './globals.css'; 

export const metadata = { 
    title: 'AEGIS — Code Integrity Analysis Platform',	
    description:	
        'Enterprise-grade platform to detect AI-generated code, scan for security vulnerabilities, and verify cryptographic authorship. Compute a Codebase Trust Score (0–100).', 
    keywords: ['AEGIS', 'AI code detection', 'code security', 'trust score', 'code integrity'], 
};	

export default function RootLayout({ children }) {	
    return ( 
        <html lang="en"> 
            <head>	
                <link rel="preconnect" href="https://fonts.googleapis.com" />	
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />	
                <link 
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" 
                    rel="stylesheet" 
                /> 
            </head> 
            <body className="bg-surface min-h-screen">{children}</body>	
        </html>	
    ); 
} 
