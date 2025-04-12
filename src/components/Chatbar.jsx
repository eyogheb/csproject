import { useState, useEffect } from 'react'
import SpeechRecognition, {useSpeechRecognition} from 'react-speech-recognition';

export function Chatbar({messages, setMessages}) {
    const [isFocused, setIsFocused] = useState(false);
    const [currentText, setText] = useState("");
    const {transcript, resetTranscript, listening} = useSpeechRecognition();

    const handleFocus = () => setIsFocused(true);
    const handleBlur = () => setIsFocused(false);
    const handleInputChange = (event) => {
        setText(event.target.value);
    };
    const handleKeyDown = (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    };
    const sendMessage = () => {
        if (currentText.trim() !== "") {
            setMessages([...messages, { text: currentText, type: "sent"}]);
            setText("");
        }
    };
    
    const handleSpeech = () => {
        resetTranscript();
        SpeechRecognition.startListening({ continuous: false, language: "en-US"});
    };

    useEffect(() => {
        if (!listening) {
            setText(transcript);
        }
    }, [listening, transcript]);

    if (!SpeechRecognition.browserSupportsSpeechRecognition()) {
        alert("Browser does not support speech recognition");
    }

    return (
        <div className = "chatBar">
            <button 
                className = "micButton"
                onClick = {handleSpeech}
            />
            <input 
                type = "text"
                value = {currentText}
                placeholder = {isFocused ? "" : "Type a message..."}
                onFocus = {handleFocus}
                onBlur = {handleBlur}
                onChange = {handleInputChange}
                onKeyDown = {handleKeyDown}
            />
            <button 
                className = "sendMessage"
                onClick = {sendMessage}
            />
        </div>
    );
}