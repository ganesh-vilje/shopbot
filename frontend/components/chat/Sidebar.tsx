"use client";
import { useState } from "react";
import { Plus, MessageSquare, Trash2, AlertTriangle, X } from "lucide-react";
import type { Conversation } from "@/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

interface DeleteModalProps {
  title: string;
  onConfirm: () => void;
  onCancel: () => void;
}

function DeleteModal({ title, onConfirm, onCancel }: DeleteModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.45)", backdropFilter: "blur(4px)" }}
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full mx-4 overflow-hidden"
        style={{ maxWidth: "380px" }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ background: "#FEF2F2" }}
            >
              <AlertTriangle size={16} style={{ color: "#C0392B" }} />
            </div>
            <span className="font-semibold text-gray-900 text-sm">
              Delete Conversation
            </span>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 transition-colors rounded-lg p-1"
            style={{color:"#9CA3AF"}}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = "#FEF2F2";
              (e.currentTarget as HTMLElement).style.color = "#C0392B";
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = "transparent";
              (e.currentTarget as HTMLElement).style.color = "#9CA3AF";
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            Are you sure you want to delete
          </p>
          <p
            className="text-sm font-medium mt-1 truncate"
            style={{ color: "#C0392B" }}
            title={title}
          >
            &quot;{title}&quot;
          </p>
          <p className="text-xs text-gray-400 mt-2">
            This action cannot be undone. All messages in this conversation will be permanently removed.
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-2 px-5 pb-5">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium text-gray-700 border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white transition-all active:scale-95"
            style={{ background: "#C0392B" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "#922B21"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "#C0392B"}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Sidebar({ conversations, activeId, onSelect, onNew, onDelete }: SidebarProps) {
  const [pendingDelete, setPendingDelete] = useState<{ id: string; title: string } | null>(null);

  function handleDeleteClick(e: React.MouseEvent, id: string, title: string) {
    e.stopPropagation();
    setPendingDelete({ id, title });
  }

  function handleConfirm() {
    if (pendingDelete) {
      onDelete(pendingDelete.id);
      setPendingDelete(null);
    }
  }

  function handleCancel() {
    setPendingDelete(null);
  }

  return (
    <>
      <aside className="hidden md:flex flex-col w-64 border-r border-gray-200 bg-gray-50 overflow-hidden" style={{ paddingTop: "64px" }}>
        <div className="p-3 pl-4">
          <button
            onClick={onNew}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-white transition-all active:scale-95"
            style={{ background: "#C0392B" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "#922B21"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "#C0392B"}
          >
            <Plus size={16} /> New Conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-4 flex flex-col">
          {conversations.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-xs text-gray-400 text-center px-4">
                No conversations yet. Start asking!
              </p>
            </div>
          ) : (
            conversations.map(c => (
              <div
                key={c.id}
                className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg mb-1 cursor-pointer transition-colors ${
                  activeId === c.id ? "text-white" : "text-gray-700 hover:bg-gray-200"
                }`}
                style={activeId === c.id ? { background: "#F9EBEA", color: "#C0392B" } : {}}
                onClick={() => onSelect(c.id)}
              >
                <MessageSquare size={14} className="flex-shrink-0" />
                <span className="text-xs flex-1 truncate font-medium">{c.title}</span>
                <button
                  onClick={e => handleDeleteClick(e, c.id, c.title)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-600 flex-shrink-0 p-0.5 rounded"
                  title="Delete conversation"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {pendingDelete && (
        <DeleteModal
          title={pendingDelete.title}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </>
  );
}