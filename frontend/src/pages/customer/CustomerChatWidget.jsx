import React, { useState, useEffect, useRef } from 'react';
import { getCustomerChat, sendCustomerChat } from '../../services/api';
import { Bot, Send, X, MessageSquare, Sparkles, User, ShieldCheck } from 'lucide-react';

export default function CustomerChatWidget({ ticketId, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChat();
  }, [ticketId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadChat = async () => {
    try {
      const res = await getCustomerChat(ticketId);
      setMessages(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const userText = input;
    setInput('');
    // Optimistic customer message
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), sender: 'customer', message: userText, created_at: new Date().toISOString() }
    ]);
    setSending(true);

    try {
      const res = await sendCustomerChat({ message: userText, ticket_id: ticketId });
      setMessages((prev) => [
        ...prev,
        { id: res.data.message_id, sender: 'ai', message: res.data.reply, created_at: res.data.created_at }
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setSending(false);
    }
  };

  const quickPrompts = [
    "When is my technician arriving?",
    "Is it safe to use the machine while waiting?",
    "Can I reschedule my appointment?"
  ];

  return (
    <div className="flex flex-col h-[520px] bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden w-full max-w-md">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-700 to-slate-900 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-teal-500/30 flex items-center justify-center border border-teal-400/40">
            <Bot className="w-5 h-5 text-teal-200" />
          </div>
          <div>
            <h3 className="text-sm font-bold flex items-center gap-1.5">
              <span>FixLoop AI Support</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </h3>
            <p className="text-[11px] text-teal-200/80">Instant answers grounded in your service history</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-lg text-slate-300 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50 text-xs">
        {messages.length === 0 && (
          <div className="text-center py-8 space-y-2 text-slate-400">
            <Bot className="w-8 h-8 mx-auto text-teal-600/50" />
            <p className="font-medium text-slate-600">Hello! How can I assist you with your repair today?</p>
            <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
              I can check technician status, explain diagnostics, or help you reschedule.
            </p>
          </div>
        )}

        {messages.map((m, idx) => {
          const isAI = m.sender === 'ai' || m.sender === 'support';
          return (
            <div key={idx} className={`flex items-start gap-2 ${isAI ? 'justify-start' : 'justify-end'}`}>
              {isAI && (
                <div className="w-6 h-6 rounded-full bg-teal-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl p-3 shadow-sm leading-relaxed ${
                  isAI
                    ? 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none'
                    : 'bg-teal-600 text-white rounded-tr-none'
                }`}
              >
                <p>{m.message}</p>
                <span className={`text-[9px] block mt-1 ${isAI ? 'text-slate-400' : 'text-teal-200'} text-right`}>
                  {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              {!isAI && (
                <div className="w-6 h-6 rounded-full bg-slate-800 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          );
        })}

        {sending && (
          <div className="flex items-center gap-2 text-slate-500">
            <div className="w-6 h-6 rounded-full bg-teal-600 text-white flex items-center justify-center">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-white p-2.5 rounded-xl rounded-tl-none border border-slate-200 shadow-sm flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-bounce [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts */}
      <div className="px-3 py-2 bg-slate-100 border-t border-slate-200 flex gap-1.5 overflow-x-auto no-scrollbar">
        {quickPrompts.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setInput(q)}
            className="text-[10px] bg-white hover:bg-teal-50 hover:text-teal-700 text-slate-600 px-2.5 py-1 rounded-full border border-slate-200 whitespace-nowrap transition"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-100 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your repair..."
          className="flex-1 text-xs border border-slate-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="p-2 bg-teal-600 hover:bg-teal-500 disabled:opacity-40 text-white rounded-xl shadow-sm transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
