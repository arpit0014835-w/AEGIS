'use client'; 

import { useState, useRef } from 'react'; 

const ACCEPTED_EXTENSIONS = [	
    '.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2', '.xz',	
    '.py', '.pyw', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', 
    '.java', '.kt', '.kts', '.scala', '.groovy', 
    '.c', '.cpp', '.h', '.hpp', '.cs', '.rs', '.go',	
    '.swift', '.dart', '.m',	
    '.rb', '.php', '.lua', '.pl', '.r', 
    '.sh', '.bash', '.ps1', '.bat', '.cmd', 
    '.html', '.htm', '.css', '.scss', '.vue', '.svelte',	
    '.json', '.yaml', '.yml', '.toml', '.xml', '.sql', '.md',	
];	

export default function ScanForm({ onSubmitUrl, onSubmitFile, loading }) { 
    const [url, setUrl] = useState(''); 
    const [dragActive, setDragActive] = useState(false); 
    const [selectedFile, setSelectedFile] = useState(null); 
    const fileInputRef = useRef(null); 

    const handleUrlSubmit = (e) => {	
        e.preventDefault();	
        if (!url.trim()) return; 
        onSubmitUrl(url.trim()); 
    };	

    const handleFileSelect = (file) => {	
        if (!file) return; 
        const name = file.name.toLowerCase(); 
        const accepted = ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));	
        if (!accepted) {	
            alert('Unsupported file type. Accepted: archives (.zip, .rar, .7z, .tar.gz) and source files (.py, .js, .java, etc.).');	
            return; 
        } 
        setSelectedFile(file);	
    }; 

    const handleDrop = (e) => {	
        e.preventDefault();	
        setDragActive(false); 
        const file = e.dataTransfer.files?.[0]; 
        handleFileSelect(file);	
    }; 

    const handleFileUpload = () => {	
        if (!selectedFile) return; 
        onSubmitFile(selectedFile);	
    };	

    return ( 
        <div className="w-full max-w-upload mx-auto"> 
            {/* GitHub URL form */}	
            <form onSubmit={handleUrlSubmit} className="mb-4"> 
                <label htmlFor="repo-url" className="block text-sm font-medium text-text-primary mb-1.5"> 
                    GitHub Repository URL 
                </label>	
                <div className="flex gap-3">	
                    <input 
                        id="repo-url" 
                        type="url"	
                        className="input-field" 
                        placeholder="https://github.com/owner/repository"	
                        value={url} 
                        onChange={(e) => setUrl(e.target.value)} 
                        disabled={loading}	
                        autoComplete="off"	
                        spellCheck={false} 
                    />	
                    <button	
                        type="submit" 
                        id="submit-url-btn"
                        className="btn-primary whitespace-nowrap"
                        disabled={loading || !url.trim()}
                    >
                        {loading ? 'Submitting...' : 'Analyze'}
                    </button>
                </div>
            </form>

            {/* OR divider */}
            <div className="flex items-center gap-4 my-5">
                <div className="flex-1 border-t border-border" />
                <span className="text-xs text-text-secondary font-medium">OR</span>
                <div className="flex-1 border-t border-border" />
            </div>

            {/* File upload */}
            <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Upload File
                </label>
                <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                    onDragLeave={() => setDragActive(false)}
                    onDrop={handleDrop}
                    className={`
                        border-2 border-dashed rounded-md px-6 py-10 text-center cursor-pointer
                        transition-colors duration-150
                        ${dragActive
                            ? 'border-primary bg-primary-light'
                            : 'border-border bg-surface hover:border-text-secondary'
                        }
                    `}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept={ACCEPTED_EXTENSIONS.join(',')}
                        className="hidden"
                        onChange={(e) => handleFileSelect(e.target.files?.[0])}
                        disabled={loading}
                    />
                    <svg
                        className="mx-auto mb-3 text-text-secondary"
                        width="24" height="24" viewBox="0 0 24 24"
                        fill="none" stroke="currentColor" strokeWidth="1.5"
                        strokeLinecap="round" strokeLinejoin="round"
                    >
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                    <p className="text-sm text-text-secondary">
                        {selectedFile
                            ? <span className="text-text-primary font-medium">{selectedFile.name}</span>
                            : 'Drop file here or click to browse'
                        }
                    </p>
                    {selectedFile && (
                        <p className="text-xs text-text-secondary mt-1">
                            {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
                        </p>
                    )}
                </div>

                {selectedFile && (
                    <button
                        id="submit-file-btn"
                        onClick={handleFileUpload}
                        className="btn-primary w-full mt-3"
                        disabled={loading}
                    >
                        {loading ? 'Uploading...' : 'Upload and Analyze'}
                    </button>
                )}
            </div>

            <p className="text-xs text-text-secondary text-center mt-5">
                Analysis typically completes in 2–5 minutes. Supports public GitHub repositories, archives (.zip, .rar, .7z, .tar.gz), and source files.
            </p>
        </div>
    );
}
