import React, { useState } from "react";
import { sendChatMessage } from "../services/api";
import { SparkleIcon, SendIcon } from "./Icons.jsx";

const GREETING = {
  role: "assistant",
  text: "Hi, I'm the LifeFlow assistant. Tell me what you need — for example \"I need B+ blood urgently\" — and I'll help set up the request.",
};

/**
 * AI Chatbot. A small guided conversation that extracts the same
 * fields as the report analyzer, one message at a time, and asks
 * for whatever is still missing. When every required field is
 * filled it offers "Use these details", which -- just like the
 * report analyzer -- only fills the normal request form below for
 * the person to review and submit themselves.
 */
export default function AIChatWidget({ onUseResult }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [slots, setSlots] = useState(null);
  const [readyToSubmit, setReadyToSubmit] = useState(false);
  const [sending, setSending] = useState(false);

  async function handleSend(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setSending(true);
    try {
      const response = await sendChatMessage(text, slots);
      setSlots(response.data.slots);
      setReadyToSubmit(response.data.ready_to_submit);
      setMessages((prev) => [...prev, { role: "assistant", text: response.data.reply }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", text: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="card ai-card">
      <button type="button" className="ai-card-toggle" onClick={() => setOpen(!open)}>
        <SparkleIcon size={18} color="#B01E28" />
        <span>AI Chatbot — describe what you need in your own words</span>
        <span className="ai-card-toggle-caret">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="ai-card-body">
          <div className="ai-chat-log">
            {messages.map((m, index) => (
              <div key={index} className={`ai-chat-bubble ${m.role}`}>{m.text}</div>
            ))}
          </div>

          {readyToSubmit && (
            <button type="button" className="inline-btn btn-outline" onClick={() => onUseResult(slots)} style={{ marginBottom: "10px" }}>
              Use these details in the form below
            </button>
          )}

          <form onSubmit={handleSend} className="ai-chat-input-row">
            <input
              type="text"
              placeholder="Type a message…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
            />
            <button type="submit" className="inline-btn" disabled={sending || !input.trim()}>
              <SendIcon size={16} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
