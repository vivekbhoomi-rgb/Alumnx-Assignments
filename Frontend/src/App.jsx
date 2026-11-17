import { useState } from "react";

export default function App() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi! Ask me about assignment submissions, e.g. 'How many times did Rohith submit?'" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send(e) {
    e.preventDefault();
    const message = input.trim();
    if (!message || loading) return;
    setMessages((m) => [...m, { role: "user", text: message }]);
    setInput("");
    setLoading(true);
    try {
      const base = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
      const res = await fetch(`${base}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      setMessages((m) => [...m, { role: "bot", text: data.reply }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "bot", text: `Error: ${err.message}` }]);
    }
    setLoading(false);
  }

  return (
    <div className="app">
      <header>Assignment Chatbot</header>
      <main>
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>{m.text}</div>
        ))}
        {loading && <div className="bubble bot">Thinking…</div>}
      </main>
      <form onSubmit={send}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question…" />
        <button disabled={loading}>Send</button>
      </form>
    </div>
  );
}
