"use client";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import type { Conversation } from "@/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export default function Sidebar({ conversations, activeId, onSelect, onNew, onDelete }: SidebarProps) {
  return (
    <aside className="hidden md:flex flex-col w-64 border-r border-gray-200 bg-gray-50 overflow-hidden" style={{paddingTop:"64px"}}>
      <div className="p-3">
        <button onClick={onNew}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-white transition-all active:scale-95"
          style={{background:"#C0392B"}}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "#922B21"}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "#C0392B"}
        >
          <Plus size={16} /> New Conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {conversations.length === 0 ? (
          <p className="text-xs text-gray-400 text-center mt-8 px-4">No conversations yet. Start asking!</p>
        ) : conversations.map(c => (
          <div key={c.id} className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg mb-1 cursor-pointer transition-colors ${activeId === c.id ? "text-white" : "text-gray-700 hover:bg-gray-200"}`}
            style={activeId === c.id ? {background:"#F9EBEA", color:"#C0392B"} : {}}
            onClick={() => onSelect(c.id)}
          >
            <MessageSquare size={14} className="flex-shrink-0" />
            <span className="text-xs flex-1 truncate font-medium">{c.title}</span>
            <button onClick={e => { e.stopPropagation(); onDelete(c.id); }}
              className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-600 flex-shrink-0">
              <Trash2 size={12} />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
