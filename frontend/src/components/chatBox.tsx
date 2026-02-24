import React, { useState, useEffect, useRef } from "react";
import { sendMessageToAgent, getConversation } from "../api/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  evaluation?: any;
  isRevised?: boolean;
}

const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [userId, setUserId] = useState<string>("");


  const messagesEndRef = useRef<HTMLDivElement>(null);

  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

 
  useEffect(() => {
    scrollToBottom();
  }, [messages]);



  
  useEffect(() => {
    let id = localStorage.getItem("career_user_id");

    if (!id) {
      id = "user_" + Math.floor(100000 + Math.random() * 900000);
      localStorage.setItem("career_user_id", id);
    }

    setUserId(id);
  }, []);

  
  useEffect(() => {
    if (!userId) return;

    const loadConversation = async () => {
      try {
        const history = await getConversation(userId);
        setMessages(history);
      } catch (err) {
        console.error("Conversation load error:", err);
      }
    };

    loadConversation();
  }, [userId]);

  const handleSend = async () => {
    if (!input.trim() || !userId) return;

    const userMessage: Message = {
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const data = await sendMessageToAgent(userId, input);

      const botMessage: Message = {
        role: "assistant",
        content: data.response,
        evaluation: data.evaluation_log,
        isRevised: data.is_revised,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("API Error:", error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  return (
    <div style={{ width: 700, margin: "40px auto" }}>
      <h2>Career Agent</h2>

      <div
        style={{
          border: "1px solid #ddd",
          height: 500,
          overflowY: "auto", 
          padding: 20,
          marginBottom: 15,
          borderRadius: 12,
          backgroundColor: "#f9f9f9",
          position: "relative"
        }}
      >
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              textAlign: msg.role === "user" ? "right" : "left",
              marginBottom: 15,
            }}
          >
            {/* Chat Bubble Area */}
            <div
              style={{
                display: "inline-block",
                padding: "10px 14px",
                borderRadius: 14,
                maxWidth: "70%",
                backgroundColor: msg.role === "user" ? "#007bff" : "#e5e5ea",
                color: msg.role === "user" ? "white" : "black",
              }}
            >
              {msg.content}
            </div>

            {/* Confidence Area (Assistant Only) */}
            {msg.role === "assistant" && msg.evaluation && (
              <div style={{ fontSize: 12, marginTop: 6, opacity: 0.8 }}>
                <div>⭐ Overall Score: {msg.evaluation.overall_score?.toFixed(1)}</div>
                <div>
                  🎯 Pro: {msg.evaluation.professional_tone} | 
                  Clarity: {msg.evaluation.clarity} | 
                  Rel: {msg.evaluation.relevance}
                </div>
                {msg.isRevised && <div style={{ color: "orange" }}>⚠ Revised Response</div>}
                {!msg.evaluation.is_acceptable && <div style={{ color: "red" }}>🚨 Escalated</div>}
              </div>
            )}
          </div>
        ))}

        
        <div ref={messagesEndRef} /> 
        </div>
      

      {/* Input Area */}
      <div style={{ display: "flex" }}>
        <input
          style={{ flex: 1, padding: 12, borderRadius: 8, border: "1px solid #ccc" }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Type a message..."
        />
        <button
          onClick={handleSend}
          style={{
            padding: "12px 20px",
            marginLeft: 10,
            borderRadius: 8,
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatBox;