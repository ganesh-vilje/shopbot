"use client";
import { useState } from "react";
import { LogOut, ShoppingBag } from "lucide-react";
import type { User as UserType } from "@/types";

interface NavbarProps { user: UserType | null; onLogout: () => void; }

export default function Navbar({ user, onLogout }: NavbarProps) {
  const [open, setOpen] = useState(false);
  const initials = user?.full_name?.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) || "U";

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm" style={{height:"64px"}}>
      <div className="h-full flex items-center justify-between px-0">
        {/* Logo */}
        <div className="flex items-center gap-2" style={{paddingLeft:"30px"}}>
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{background:"#C0392B"}}>
            <ShoppingBag size={20} color="white" />
          </div>
          <span className="text-xl font-bold" style={{color:"#C0392B", letterSpacing:"-0.02em"}}>ShopBot</span>
        </div>

        {/* Profile button - popover trigger */}
        <div className="relative" style={{paddingRight:"30px"}}>
          <button
            onClick={() => setOpen(o => !o)}
            className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-gray-100 transition-colors"
          >
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold text-white" style={{background:"#C0392B"}}>
              {initials}
            </div>
          </button>

          {open && (
            <div className="absolute right-0 top-14 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="font-semibold text-gray-900 text-sm">{user?.full_name}</p>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{user?.email}</p>
              </div>
              <button
                onClick={() => { setOpen(false); onLogout(); }}
                className="w-full flex items-center gap-2 px-4 py-4 text-sm text-left hover:bg-red-50 transition-colors font-medium"
                style={{color:"#C0392B"}}
              >
                <LogOut size={16} />
                Log out
              </button>
            </div>
          )}
        </div>
      </div>

      {open && <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />}
    </header>
  );
}
