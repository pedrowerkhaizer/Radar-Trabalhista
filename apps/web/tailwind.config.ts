import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: ["class"],
    content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			brand: {
  				50: '#EFF6FF',
  				100: '#DBEAFE',
  				200: '#BFDBFE',
  				300: '#93C5FD',
  				400: '#60A5FA',
  				500: '#3B82F6',
  				600: '#2563EB',
  				700: '#1D4ED8',
  				800: '#1E40AF',
  				900: '#1E3A8A',
  			},
  			success: {
  				DEFAULT: '#059669',
  				light: '#D1FAE5',
  				text: '#065F46',
  			},
  			danger: {
  				DEFAULT: '#DC2626',
  				light: '#FEE2E2',
  				text: '#991B1B',
  			},
  			warning: {
  				DEFAULT: '#D97706',
  				light: '#FEF3C7',
  				text: '#92400E',
  			},
  			slate: {
  				50: '#F8FAFC',
  				100: '#F1F5F9',
  				200: '#E2E8F0',
  				300: '#CBD5E1',
  				400: '#94A3B8',
  				500: '#64748B',
  				600: '#475569',
  				700: '#334155',
  				800: '#1E293B',
  				900: '#0F172A',
  			}
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		boxShadow: {
  			'card': '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
  			'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.07)',
  			'lg': '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.05)',
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
