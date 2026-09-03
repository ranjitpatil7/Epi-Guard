import type { Variants } from "framer-motion"

export const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    }
  }
}

export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 25, scale: 0.98 },
  show: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { 
      type: "spring", 
      stiffness: 400, 
      damping: 30,
      mass: 0.8
    } 
  }
}

export const chartTooltipStyle = {
  backgroundColor: 'rgba(9, 9, 11, 0.85)',
  backdropFilter: 'blur(16px)',
  borderColor: 'rgba(255, 255, 255, 0.1)',
  borderRadius: '16px',
  boxShadow: '0 12px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
  color: '#fafafa',
  padding: '16px',
  border: '1px solid rgba(255, 255, 255, 0.1)'
}

export const chartColors = {
  primary: '#3b82f6',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#e11d48',
  indigo: '#4f46e5',
  slate: '#94a3b8',
  gridLine: 'rgba(255, 255, 255, 0.05)'
}
