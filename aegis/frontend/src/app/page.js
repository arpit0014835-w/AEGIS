'use client'; 

import { useState } from 'react'; 
import { useRouter } from 'next/navigation';	
import Navbar from '@/components/Navbar';	
import ScanForm from '@/components/ScanForm'; 
import { submitScan, uploadScan } from '@/lib/api'; 

export default function HomePage() {	
    const router = useRouter();	
    const [loading, setLoading] = useState(false); 
    const [error, setError] = useState(''); 

    const handleUrlSubmit = async (url) => {	
        setLoading(true);	
        setError('');	
        try { 
            const result = await submitScan(url); 
            router.push(`/dashboard/${result.scan_id}`); 
        } catch (e) { 
            setError(e.message); 
        } finally {	
            setLoading(false);	
        } 
    }; 

    const handleFileSubmit = async (file) => {	
        setLoading(true);	
        setError(''); 
        try { 
            const result = await uploadScan(file);	
            router.push(`/dashboard/${result.scan_id}`);	
        } catch (e) {	
            setError(e.message); 
        } finally { 
            setLoading(false);	
        } 
    };	

    return (	
        <> 
            <Navbar /> 

            <main className="min-h-[calc(100vh-56px)] flex flex-col items-center justify-center px-6 py-16">	

                {/* Logo + description block */} 
                <div className="w-full max-w-upload text-center mb-10">	
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-xl mb-5 shadow-sm"> 
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">	
                            <path	
                                d="M16 3L4 8.5V17C4 23.075 9.4 28.775 16 30C22.6 28.775 28 23.075 28 17V8.5L16 3Z" 
                                fill="white" fillOpacity="0.15" stroke="white" strokeWidth="1.5" 
                                strokeLinejoin="round"	
                            /> 
                            <path 
                                d="M11 16.5L14.5 20L21 13" 
                                stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"	
                            />	
                        </svg> 
                    </div> 

                    <h1 className="text-4xl font-bold tracking-tight text-text-primary mb-3">	
                        AEGIS 
                    </h1>	
                    <p className="text-base text-text-secondary max-w-md mx-auto leading-relaxed"> 
                        AI-Generated Code Trust Framework. Detect AI-written code, scan for AI-specific 
                        vulnerabilities, and verify cryptographic authorship — all in a single Trust Score.	
                    </p>	
                    <div className="flex items-center justify-center gap-3 mt-4"> 
                        <span className="badge badge-primary">Ghost Detect</span>	
                        <span className="badge badge-neutral">Breach Secure</span>	
                        <span className="badge badge-success">Proof Verify</span> 
                    </div>
                </div>

                {/* Divider */}
                <div className="w-full max-w-upload border-t border-border mb-8" />

                {/* Form card */}
                <div className="w-full max-w-upload card p-8">
                    <h2 className="text-base font-semibold text-text-primary mb-6">Analyze Repository</h2>
                    <ScanForm
                        onSubmitUrl={handleUrlSubmit}
                        onSubmitFile={handleFileSubmit}
                        loading={loading}
                    />

                    {error && (
                        <div
                            id="scan-error"
                            className="mt-4 px-4 py-3 rounded-md bg-danger-light border border-danger/20 text-sm text-danger"
                        >
                            {error}
                        </div>
                    )}
                </div>

                {/* Platform pillars — text only, no icons */}
                <div className="w-full max-w-upload mt-10 grid grid-cols-3 gap-4">
                    {[
                        {
                            title: 'Ghost Detect',
                            weight: '35%',
                            desc: 'Style consistency modelling and hallucinated dependency detection.',
                        },
                        {
                            title: 'Breach Secure',
                            weight: '40%',
                            desc: 'AI-aware static analysis with prompt injection fuzzing.',
                        },
                        {
                            title: 'Proof Verify',
                            weight: '25%',
                            desc: 'SHA-256 cryptographic authorship watermark verification.',
                        },
                    ].map((p) => (
                        <div key={p.title} className="card p-5">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm font-semibold text-text-primary">{p.title}</p>
                                <span className="badge badge-primary">{p.weight}</span>
                            </div>
                            <p className="text-xs text-text-secondary leading-relaxed">{p.desc}</p>
                        </div>
                    ))}
                </div>
            </main>
        </>
    );
}
