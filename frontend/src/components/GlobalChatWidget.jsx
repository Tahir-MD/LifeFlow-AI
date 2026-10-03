import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { sendChatMessage } from "../services/api";
import { RobotIcon, SendIcon } from "./Icons.jsx";

const GREETING = {
  role: "assistant",
  text: "Hi! I'm the LifeFlow assistant. Tell me what you need — e.g. \"I need B+ blood urgently\" — and I'll help set up the request.",
};

const PENDING_REQUEST_KEY = "lifeflow_ai_pending_request";

/**
 * The AI Chatbot, available everywhere (including signed-out, on the
 * home page) as a floating robot button in the bottom-right corner.
 * It has the same guided conversation as the inline widget on the
 * request forms; when it has everything it needs, it saves those
 * details and sends the person to the right dashboard to review and
 * submit the actual request themselves -- this widget never creates
 * one on its own.
 */
export default function GlobalChatWidget() {
  const navigate = useNavigate();
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

  function handleContinue() {
    localStorage.setItem(PENDING_REQUEST_KEY, JSON.stringify(slots));
    const role = localStorage.getItem("lifeflow_role");
    setOpen(false);
    if (role === "hospital") {
      navigate("/hospital/dashboard");
    } else if (role === "receiver") {
      navigate("/receiver/dashboard");
    } else {
      navigate("/receiver/login");
    }
  }

  return (
    <div className="global-chat-widget">
      {open && (
        <div className="global-chat-panel">
          <div className="global-chat-header">
            <RobotIcon size={20} color="#FFFFFF" />
            <span>LifeFlow Assistant</span>
            <button type="button" className="global-chat-close" onClick={() => setOpen(false)}>×</button>
          </div>
          <div className="ai-chat-log">
            {messages.map((m, index) => (
              <div key={index} className={`ai-chat-bubble ${m.role}`}>{m.text}</div>
            ))}
          </div>
          {readyToSubmit && (
            <button type="button" className="inline-btn btn-outline" onClick={handleContinue} style={{ margin: "0 14px 10px" }}>
              Continue to the request form
            </button>
          )}
          <form onSubmit={handleSend} className="ai-chat-input-row" style={{ padding: "0 14px 14px" }}>
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

      <button
        type="button"
        className="global-chat-fab"
        onClick={() => setOpen(!open)}
        aria-label="Open LifeFlow AI assistant"
      >
        <RobotIcon size={28} color="#FFFFFF" />
      </button>
    </div>
  );
}

export { PENDING_REQUEST_KEY };
