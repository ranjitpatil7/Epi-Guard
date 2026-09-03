import { useState, useEffect } from "react"
import { Bell, Search, User, Sun, Moon } from "lucide-react"

export function TopNav() {
  const [fieldMode, setFieldMode] = useState(false)

  useEffect(() => {
    // Check local storage or default to false
    const saved = localStorage.getItem("fieldMode") === "true"
    setFieldMode(saved)
    if (saved) {
      document.documentElement.classList.add("field-mode")
    }
  }, [])

  const toggleFieldMode = () => {
    const newState = !fieldMode
    setFieldMode(newState)
    localStorage.setItem("fieldMode", String(newState))
    if (newState) {
      document.documentElement.classList.add("field-mode")
    } else {
      document.documentElement.classList.remove("field-mode")
    }
  }

  return (
    <header className="flex h-16 shrink-0 items-center gap-x-4 border-b border-white/10 bg-black/20 backdrop-blur-2xl px-4 sm:gap-x-6 sm:px-6 lg:px-8 z-10 sticky top-0 relative shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <form className="relative flex flex-1 items-center group" action="#" method="GET">
          <label htmlFor="search-field" className="sr-only">
            Search
          </label>
          <Search
            className="pointer-events-none absolute left-0 h-5 w-5 text-muted-foreground/50 transition-colors group-focus-within:text-primary"
            aria-hidden="true"
          />
          <input
            id="search-field"
            className="block h-full w-full border-0 bg-transparent py-0 pl-8 pr-0 text-foreground placeholder:text-muted-foreground/50 focus:ring-0 sm:text-sm outline-none transition-all focus:pl-10 font-medium"
            placeholder="Global search (Ctrl+K)..."
            type="search"
            name="search"
          />
        </form>
        <div className="flex items-center gap-x-4 lg:gap-x-6">
          <div className="hidden sm:flex flex-col items-end mr-2 text-[11px] font-medium text-muted-foreground">
            <span className="text-primary tracking-wide uppercase drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]">Operational</span>
            <span className="opacity-70">&lt; 5 mins fresh</span>
          </div>

          <button 
            type="button" 
            onClick={toggleFieldMode}
            className="-m-2.5 p-2.5 text-muted-foreground hover:text-primary transition-colors relative"
            title="Toggle Field Mode (High Contrast)"
          >
            <span className="sr-only">Toggle Field Mode</span>
            {fieldMode ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          </button>

          <button type="button" className="-m-2.5 p-2.5 text-muted-foreground hover:text-primary transition-colors relative">
            <span className="sr-only">View notifications</span>
            <Bell className="h-5 w-5" aria-hidden="true" />
            <span className="absolute top-2.5 right-2.5 block h-2 w-2 rounded-full bg-destructive border-2 border-black/40 shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
          </button>

          {/* Separator */}
          <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-white/10" aria-hidden="true" />

          {/* Profile dropdown stub */}
          <div className="flex items-center gap-x-4">
            <div className="flex items-center gap-x-3 cursor-pointer group">
              <div className="h-9 w-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center group-hover:bg-primary/20 group-hover:border-primary/50 transition-all duration-300 shadow-sm group-hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                <User className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              <span className="hidden lg:flex lg:items-center">
                <span className="text-sm font-semibold leading-6 text-foreground group-hover:text-primary transition-colors" aria-hidden="true">
                  Health Official
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
