import { ShoppingBag, Search, Package, Star, HelpCircle } from "lucide-react";

const SUGGESTIONS = [
  { icon: <Package size={16}/>, text: "Where is my latest order?" },
  { icon: <Search size={16}/>, text: "Show me the best laptops you have" },
  { icon: <Star size={16}/>, text: "What are your top-rated products?" },
  { icon: <HelpCircle size={16}/>, text: "What is your return policy?" },
];

export default function WelcomeScreen({ name, onSuggest }: { name: string; onSuggest: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-4 py-16 text-center">
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-lg" style={{background:"#C0392B"}}>
        <ShoppingBag size={32} color="white" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Hello, {name?.split(" ")[0] || "there"}! 👋
      </h2>
      <p className="text-gray-500 text-sm max-w-xs mb-8">
        I&apos;m Alex, your ShopBot assistant. Ask me anything about your orders, products, or account!
      </p>
      <div className="grid grid-cols-1 gap-2 w-full max-w-sm">
        {/* {SUGGESTIONS.map((s, i) => (
          <button key={i} onClick={() => onSuggest(s.text)}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-left text-sm font-medium text-gray-700 hover:text-gray-900 transition-all hover:shadow-md"
            style={{background:"#F9EBEA", border:"1px solid #F5C6C3"}}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = "#C0392B"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = "#F5C6C3"}
          >
            <span style={{color:"#C0392B"}}>{s.icon}</span>
            {s.text}
          </button>
        ))} */}
      </div>
    </div>
  );
}
