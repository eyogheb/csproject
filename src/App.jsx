import { useEffect, useRef, useState } from 'react'
import { Header } from './components/Header.jsx'
import { Chatbar } from './components/Chatbar.jsx'
import { Messagelist } from './components/Messagelist.jsx'
import axios from 'axios'
import './App.css'

function App() {
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);
  const introMessage = "Hello! Ronald is an AI chatbot that is able to take your order and answer any questions about the menu using text or speech.";
  const sendMessage = async (message) => {
    try {
      const response = await axios.post("https://18.217.78.63:8000/chat", {message: message});
      const newMessage = response.data.content;

      setMessages([...messages, {text: newMessage, type: "received"}]);

    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    
    if (latestMessage?.type === "sent") {
      sendMessage(latestMessage.text);
    }
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
  }, [messages]);

  useEffect(() => {
    setMessages([...messages, {text: introMessage, type: "received"}]);
  }, []);

  return (
    <div className="card">
      <Header />
      <hr className="divider" />
      <div className="chatBox">
        <Messagelist messages = {messages} messageRef = {messagesEndRef} />
      </div>
      <hr className="divider-2" />
      <Chatbar messages = {messages} setMessages = {setMessages} />
    </div>
  );
}

export default App
