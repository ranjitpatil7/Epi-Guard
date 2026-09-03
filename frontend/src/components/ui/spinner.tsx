import * as React from "react"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "default" | "lg"
}

export function Spinner({ className, size = "default", ...props }: SpinnerProps) {
  const sizes = {
    sm: "h-4 w-4",
    default: "h-8 w-8",
    lg: "h-12 w-12"
  }
  
  return (
    <div className={cn("flex justify-center items-center", className)} {...props}>
      <Loader2 className={cn("animate-spin text-primary", sizes[size])} />
    </div>
  )
}
