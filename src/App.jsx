import { useEffect, useRef, useState } from 'react'
import { Header } from './components/Header.jsx'
import { Chatbar } from './components/Chatbar.jsx'
import { Messagelist } from './components/Messagelist.jsx'
import './App.css'

function App() {
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
  }, [messages]);

  return (
    <div className="card">
      <Header />
      <div className="chatBox">
        <Messagelist messages = {messages} messageRef = {messagesEndRef} />
      </div>
      <Chatbar messages = {messages} setMessages = {setMessages} />
    </div>
  );
}

export default App
