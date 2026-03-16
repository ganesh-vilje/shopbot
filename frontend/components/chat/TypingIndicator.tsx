export default function TypingIndicator() {
  return (
    <div className="flex gap-3 mb-4 message-enter">
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" style={{background:"#C0392B"}}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/>
          <path d="M16 10a4 4 0 01-8 0"/>
        </svg>
      </div>
      <div className="px-4 py-3 rounded-2xl rounded-tl-sm" style={{background:"#F9EBEA", border:"1px solid #F5C6C3"}}>
        <div className="flex items-center gap-1 h-5">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  );
}
