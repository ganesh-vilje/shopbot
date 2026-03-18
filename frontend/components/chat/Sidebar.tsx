"use client";
import { useRef, useState } from "react";
import { Plus, MessageSquare, Trash2, AlertTriangle, X, Menu, Pencil, Search, PenSquare } from "lucide-react";
import type { Conversation } from "@/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, title: string) => Promise<void>;
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

interface RenameModalProps {
  value: string;
  loading: boolean;
  error: string;
  onChange: (value: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

function RenameModal({
  value,
  loading,
  error,
  onChange,
  onConfirm,
  onCancel,
}: RenameModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.45)", backdropFilter: "blur(4px)" }}
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full mx-4 overflow-hidden"
        style={{ maxWidth: "420px" }}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ background: "#F9EBEA" }}
            >
              <Pencil size={15} style={{ color: "#C0392B" }} />
            </div>
            <span className="font-semibold text-gray-900 text-sm">
              Rename Conversation
            </span>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 transition-colors rounded-lg p-1"
            style={{ color: "#9CA3AF" }}
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-5 py-4">
          <input
            type="text"
            value={value}
            onChange={e => onChange(e.target.value)}
            onKeyDown={e => {
              if (e.key === "Enter") onConfirm();
            }}
            className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-800 focus:outline-none"
            style={{ borderColor: "#F5C6C3" }}
            autoFocus
            maxLength={255}
          />
          {error && <p className="mt-2 text-xs" style={{ color: "#C0392B" }}>{error}</p>}
        </div>

        <div className="flex gap-2 px-5 pb-5">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium text-gray-700 border border-gray-200 hover:bg-gray-50 transition-colors"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white transition-all active:scale-95 disabled:opacity-60"
            style={{ background: "#C0392B" }}
            disabled={loading}
          >
            {loading ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

interface SearchChatsModalProps {
  conversations: Conversation[];
  onClose: () => void;
  onSelect: (id: string) => void;
  onNew: () => void;
}

function SearchChatsModal({
  conversations,
  onClose,
  onSelect,
  onNew,
}: SearchChatsModalProps) {
  const [query, setQuery] = useState("");

  const filteredConversations = conversations.filter(conversation =>
    conversation.title.toLowerCase().includes(query.trim().toLowerCase())
  );
  const sections = groupConversationsByDate(filteredConversations);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-20"
      style={{ background: "rgba(0,0,0,0.45)", backdropFilter: "blur(4px)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center border-b border-gray-200 px-5 py-4">
          <Search size={18} className="mr-3 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search chats..."
            className="flex-1 bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none"
            autoFocus
          />
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-red-400 transition-colors hover:bg-red-100 hover:text-gray-600"
            aria-label="Close search"
          >
            <X size={18} />
          </button>
        </div>

        <div className="max-h-[65vh] overflow-y-auto p-3">
          <button
            onClick={() => {
              onNew();
              onClose();
            }}
            className="mb-3 flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
            style={{ background: "#F9EBEA" }}
          >
            <PenSquare size={16} style={{ color: "#C0392B" }} />
            New chat
          </button>

          {sections.length === 0 ? (
            <div className="px-3 py-10 text-center text-sm text-gray-400">
              No chats found for your search.
            </div>
          ) : (
            sections.map(section => (
              <div key={section.label} className="mb-5">
                <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  {section.label}
                </p>
                <div className="space-y-1">
                  {section.items.map(conversation => (
                    <button
                      key={conversation.id}
                      onClick={() => {
                        onSelect(conversation.id);
                        onClose();
                      }}
                      className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm text-gray-700 transition-colors hover:bg-gray-100"
                    >
                      <MessageSquare size={16} className="flex-shrink-0 text-gray-400" />
                      <span className="truncate font-medium">{conversation.title}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function groupConversationsByDate(conversations: Conversation[]) {
  const now = new Date();
  const today: Conversation[] = [];
  const previousSevenDays: Conversation[] = [];
  const older: Conversation[] = [];

  for (const conversation of conversations) {
    const updatedAt = new Date(conversation.updated_at);
    const diffDays = Math.floor((now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60 * 24));

    if (updatedAt.toDateString() === now.toDateString()) {
      today.push(conversation);
    } else if (diffDays <= 7) {
      previousSevenDays.push(conversation);
    } else {
      older.push(conversation);
    }
  }

  return [
    { label: "Today", items: today },
    { label: "Previous 7 Days", items: previousSevenDays },
    { label: "Older", items: older },
  ].filter(section => section.items.length > 0);
}

export default function Sidebar({ conversations, activeId, onSelect, onNew, onDelete, onRename }: SidebarProps) {
  const [pendingDelete, setPendingDelete] = useState<{ id: string; title: string } | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [pendingRename, setPendingRename] = useState<{ id: string; title: string } | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [renameError, setRenameError] = useState("");
  const [renameLoading, setRenameLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const successHideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const successClearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function showSuccess(message: string) {
    if (successHideTimerRef.current) clearTimeout(successHideTimerRef.current);
    if (successClearTimerRef.current) clearTimeout(successClearTimerRef.current);

    setSuccessMessage(message);
    setShowSuccessToast(true);

    successHideTimerRef.current = setTimeout(() => {
      setShowSuccessToast(false);
    }, 2200);

    successClearTimerRef.current = setTimeout(() => {
      setSuccessMessage("");
    }, 2500);
  }

  function dismissSuccess() {
    if (successHideTimerRef.current) clearTimeout(successHideTimerRef.current);
    if (successClearTimerRef.current) clearTimeout(successClearTimerRef.current);

    setShowSuccessToast(false);
    successClearTimerRef.current = setTimeout(() => {
      setSuccessMessage("");
    }, 220);
  }
  const [searchOpen, setSearchOpen] = useState(false);

  function handleDeleteClick(e: React.MouseEvent, id: string, title: string) {
    e.stopPropagation();
    setPendingDelete({ id, title });
  }

  function handleRenameClick(e: React.MouseEvent, id: string, title: string) {
    e.stopPropagation();
    setPendingRename({ id, title });
    setRenameValue(title);
    setRenameError("");
  }

  function handleConfirm() {
    if (pendingDelete) {
      onDelete(pendingDelete.id);
      setPendingDelete(null);
      showSuccess("Deleted successfully");
    }
  }

  function handleCancel() {
    setPendingDelete(null);
  }

  function handleRenameCancel() {
    setPendingRename(null);
    setRenameValue("");
    setRenameError("");
    setRenameLoading(false);
  }

  async function handleRenameConfirm() {
    if (!pendingRename) return;

    const nextTitle = renameValue.trim();
    if (!nextTitle) {
      setRenameError("Conversation title cannot be empty");
      return;
    }

    try {
      setRenameLoading(true);
      setRenameError("");
      await onRename(pendingRename.id, nextTitle);
      showSuccess("Renamed successfully");
      handleRenameCancel();
    } catch (error) {
      setRenameError(error instanceof Error ? error.message : "Failed to rename conversation");
      setRenameLoading(false);
    }
  }

  function handleSelectConversation(id: string) {
    onSelect(id);
    setMobileOpen(false);
  }

  function handleNewConversation() {
    onNew();
    setMobileOpen(false);
  }

  const sidebarContent = (
    <>
      <div className="p-3 pl-4">
        <button
          onClick={handleNewConversation}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-white transition-all active:scale-95"
          style={{ background: "#C0392B" }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "#922B21"}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "#C0392B"}
        >
          <Plus size={16} /> New Conversation
        </button>
        <button
          onClick={() => setSearchOpen(true)}
          className="mt-2 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200"
        >
          <Search size={16} />
          Search chats
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
              className={`group relative flex items-center gap-2 px-3 py-2.5 rounded-lg mb-1 cursor-pointer transition-colors ${
                activeId === c.id ? "text-white" : "text-gray-700 hover:bg-gray-200"
              }`}
              style={activeId === c.id ? { background: "#F9EBEA", color: "#C0392B" } : {}}
              onClick={() => handleSelectConversation(c.id)}
            >
              <MessageSquare size={14} className="flex-shrink-0" />
              <span className="text-xs flex-1 truncate font-medium">{c.title}</span>
              <div className="relative flex-shrink-0">
                <button
                  onClick={e => handleRenameClick(e, c.id, c.title)}
                  className="group/rename opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity hover:text-red-600 p-0.5 rounded"
                  aria-label="Rename conversation"
                >
                  <Pencil size={12} />
                  <span
                    className="pointer-events-none absolute right-0 -top-8 z-20 whitespace-nowrap rounded-md bg-black px-2 py-1 text-[11px] text-white opacity-0 transition-opacity duration-150 md:group-hover/rename:opacity-100"
                  >
                    Rename
                  </span>
                </button>
              </div>
              <div className="relative flex-shrink-0">
                <button
                  onClick={e => handleDeleteClick(e, c.id, c.title)}
                  className="group/delete opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity hover:text-red-600 p-0.5 rounded"
                  aria-label="Delete conversation"
                >
                  <Trash2 size={12} />
                  <span
                    className="pointer-events-none absolute right-0 -top-8 z-20 whitespace-nowrap rounded-md bg-black px-2 py-1 text-[11px] text-white opacity-0 transition-opacity duration-150 md:group-hover/delete:opacity-100"
                  >
                    Delete
                  </span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );

  return (
    <>
      <button
        onClick={() => setMobileOpen(true)}
        className="md:hidden fixed left-4 z-40 rounded-xl p-2.5 shadow-lg border border-gray-200 bg-white"
        style={{ top: "78px" }}
        aria-label="Open conversations"
      >
        <Menu size={18} style={{ color: "#C0392B" }} />
      </button>

      <aside className="hidden md:flex flex-col w-64 border-r border-gray-200 bg-gray-50 overflow-hidden" style={{ paddingTop: "64px" }}>
        {sidebarContent}
      </aside>

      {mobileOpen && (
        <>
          <div
            className="md:hidden fixed inset-0 z-40"
            style={{ background: "rgba(0,0,0,0.35)" }}
            onClick={() => setMobileOpen(false)}
          />
          <aside
            className="md:hidden fixed top-0 left-0 bottom-0 z-50 w-72 max-w-[85vw] bg-gray-50 border-r border-gray-200 flex flex-col shadow-2xl"
            style={{ paddingTop: "64px" }}
          >
            <div className="flex items-center justify-end px-3 pt-3">
              <button
                onClick={() => setMobileOpen(false)}
                className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-200 transition-colors"
                aria-label="Close conversations"
              >
                <X size={18} />
              </button>
            </div>
            {sidebarContent}
          </aside>
        </>
      )}

      {pendingDelete && (
        <DeleteModal
          title={pendingDelete.title}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}

      {pendingRename && (
        <RenameModal
          value={renameValue}
          loading={renameLoading}
          error={renameError}
          onChange={setRenameValue}
          onConfirm={handleRenameConfirm}
          onCancel={handleRenameCancel}
        />
      )}

      {successMessage && (
        <div
          className={`fixed bottom-3 left-3 z-30 flex max-w-[calc(100vw-1.5rem)] items-center gap-3 rounded-xl border px-4 py-2.5 text-sm font-medium shadow-lg md:absolute md:max-w-[220px] ${
            showSuccessToast ? "sidebar-toast-enter" : "sidebar-toast-exit"
          }`}
          style={{
            background: "#2F302C",
            borderColor: "rgba(255,255,255,0.22)",
            color: "#F8F8F7",
          }}
        >
          <Info size={14} />
          <span className="flex-1 whitespace-nowrap">{successMessage}</span>
          <button
            onClick={dismissSuccess}
            className="rounded-md p-0.5 transition-colors"
            aria-label="Close notification"
            style={{ color: "rgba(255,255,255,0.8)" }}
          >
            <X size={14} />
          </button>
        </div>
      )}
      <style jsx>{`
        .sidebar-toast-enter {
          animation: sidebarToastIn 0.22s ease-out forwards;
        }

        .sidebar-toast-exit {
          animation: sidebarToastOut 0.22s ease-in forwards;
        }

        @keyframes sidebarToastIn {
          from {
            opacity: 0;
            transform: translateX(-14px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes sidebarToastOut {
          from {
            opacity: 1;
            transform: translateX(0);
          }
          to {
            opacity: 0;
            transform: translateX(-14px);
          }
        }
      `}</style>
      {searchOpen && (
        <SearchChatsModal
          conversations={conversations}
          onClose={() => setSearchOpen(false)}
          onSelect={id => {
            handleSelectConversation(id);
            setSearchOpen(false);
          }}
          onNew={() => {
            handleNewConversation();
            setSearchOpen(false);
          }}
        />
      )}
    </>
  );
}
