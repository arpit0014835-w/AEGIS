/** @type {import('tailwindcss').Config} */ 
module.exports = { 
    content: [	
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',	
        './src/components/**/*.{js,ts,jsx,tsx,mdx}', 
        './src/app/**/*.{js,ts,jsx,tsx,mdx}', 
    ],	
    theme: {	
        extend: { 
            fontFamily: { 
                sans: ['Inter', 'system-ui', 'sans-serif'],	
                mono: ['JetBrains Mono', 'Menlo', 'monospace'],	
            },	
            colors: { 
                // AEGIS design system palette 
                surface: '#F8FAFC', 
                card: '#FFFFFF', 
                border: '#E2E8F0', 
                'text-primary': '#0F172A',	
                'text-secondary': '#475569',	
                primary: '#2563EB', 
                'primary-hover': '#1D4ED8', 
                success: '#16A34A',	
                warning: '#D97706',	
                danger: '#DC2626', 
                'danger-light': '#FEF2F2', 
                'warning-light': '#FFFBEB',	
                'success-light': '#F0FDF4',	
                'primary-light': '#EFF6FF',	
            }, 
            maxWidth: { 
                container: '72rem', // 1152px	
                upload: '56rem',    // 896px 
            },	
        },	
    }, 
    plugins: [], 
};	
