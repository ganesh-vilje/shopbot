"use client";
import { useState } from "react";
import { LogOut, User, ChevronDown, ShoppingBag } from "lucide-react";
import type { User as UserType } from "@/types";

interface NavbarProps { user: UserType | null; onLogout: () => void; }

export default function Navbar({ user, onLogout }: NavbarProps) {
  const [open, setOpen] = useState(false);
  const initials = user?.full_name?.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) || "U";

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm" style={{height:"64px"}}>
      <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{background:"#C0392B"}}>
            <ShoppingBag size={20} color="white" />
          </div>
          <span className="text-xl font-bold" style={{color:"#C0392B", letterSpacing:"-0.02em"}}>ShopBot</span>
        </div>

        {/* Profile dropdown */}
        <div className="relative">
          <button
            onClick={() => setOpen(o => !o)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold text-white" style={{background:"#C0392B"}}>
              {initials}
            </div>
            <ChevronDown size={16} className="text-gray-500" style={{transform: open ? "rotate(180deg)" : "none", transition:"transform 0.2s"}} />
          </button>

          {open && (
            <div className="absolute right-0 top-12 w-64 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden z-50">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="font-semibold text-gray-900 text-sm">{user?.full_name}</p>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{user?.email}</p>
                <div className="flex items-center gap-1 mt-2">
                  <span className="text-xs px-2 py-0.5 rounded-full font-medium text-white" style={{background:"#C0392B"}}>
                    ⭐ {user?.loyalty_points ?? 0} pts
                  </span>
                </div>
              </div>
              <button
                onClick={() => { setOpen(false); onLogout(); }}
                className="w-full flex items-center gap-2 px-4 py-3 text-sm text-left hover:bg-red-50 transition-colors"
                style={{color:"#C0392B"}}
              >
                <LogOut size={16} />
                <span className="font-medium">Log out</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {open && <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />}
    </header>
  );
}
