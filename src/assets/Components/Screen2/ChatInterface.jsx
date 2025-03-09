import React, { useState, useRef, useEffect } from "react";
function ChatInterface({ domain, resumeText, onMessageCountUpdate }) {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [isTyping, setIsTyping] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const recognitionRef = useRef(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const API_KEY = "teri api key aayegi";
  const API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";
  useEffect(() => {
    scrollToBottom();
    if (onMessageCountUpdate) {
      onMessageCountUpdate(messages.length);
    }
  }, [messages, onMessageCountUpdate]);
  useEffect(() => {
    getFirstQuestion();
  }, []);
  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        if (finalTranscript !== '') {
          setUserInput(prevInput => prevInput + finalTranscript + ' ');
        }
        setTranscript(interimTranscript);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        if (isListening) {
          recognitionRef.current.start();
        }
      };
    } else {
      console.warn('Speech recognition not supported in this browser.');
    }
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isListening]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  const speakMessage = (text, onEnd) => {
    window.speechSynthesis.cancel();
    
    setIsSpeaking(true);
    const utterance = new SpeechSynthesisUtterance(text);
    
    utterance.onend = () => {
      setIsSpeaking(false);
      if (onEnd) onEnd();
    };
    
    window.speechSynthesis.speak(utterance);
  };
  const getFirstQuestion = async () => {
    try {
      const initialPrompt = `
You are an AI interviewer conducting a job interview for a position in the ${domain} field.
The candidate's resume information is provided below:
${resumeText}

Please begin by greeting the candidate warmly and asking them to tell you about themselves. Your response should be concise (1-2 sentences) and only ask for a brief self-introduction. Do not include any additional follow-up questions until after the candidate has responded.
`;
      const response = await fetch(`${API_URL}?key=${API_KEY}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: initialPrompt }] }]
        })
      });
      const data = await response.json();
      const aiMessage = data.candidates[0].content.parts[0].text || `Welcome to your ${domain} interview! Can you tell me about your background in this field?`;
      setMessages([{ sender: "ai", text: aiMessage }]);
      setTimeout(() => {
        speakMessage(aiMessage, () => {
          setIsTyping(false);
        });
      }, 100);
    } catch (error) {
      console.error("Error fetching initial question:", error);
      const fallbackMessage = `Welcome to your ${domain} interview! Can you tell me about your background in this field?`;
      setMessages([{ sender: "ai", text: fallbackMessage }]);
      setTimeout(() => {
        speakMessage(fallbackMessage, () => {
          setIsTyping(false);
        });
      }, 100);
    }
  };
  const generateAIResponse = async (conversation) => {
    try {
      setIsTyping(true);
      const prompt = `
You are an AI interviewer conducting a job interview for a position in the ${domain} field.
The candidate has submitted their resume, and here is the extracted information:
${resumeText}
Based on this resume information and the conversation so far, ask a relevant follow-up question or a new interview question that specifically relates to the candidate's experience with ${domain}.
Ask technical questions relevant to the ${domain} field that would assess the candidate's knowledge and skills.
Your responses should be concise (1-3 sentences) and professional.
Here's the conversation so far:
${conversation}
Provide only your next question as the interviewer.`;
      const response = await fetch(`${API_URL}?key=${API_KEY}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }]
        })
      });
      const data = await response.json();
      return data.candidates[0].content.parts[0].text || "Could you elaborate more on your experience with that technology?";
    } catch (error) {
      console.error("Error generating AI response:", error);
      return `That's interesting. Can you tell me about a challenging project you worked on in this field?`;
    }
  };
  const handleAIResponse = async (userText) => {
    const updatedMessages = messages.concat({ sender: "user", text: userText });
    const conversationHistory = updatedMessages
      .map(msg => `${msg.sender === "ai" ? "Interviewer" : "Candidate"}: ${msg.text}`)
      .join("\n");
    const aiResponse = await generateAIResponse(conversationHistory);
    setMessages([...updatedMessages, { sender: "ai", text: aiResponse }]);
    setIsTyping(false);
    setTimeout(() => {
      speakMessage(aiResponse);
    }, 100);
  };
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (userInput.trim() === "") return;
    setMessages((prevMessages) => [...prevMessages, { sender: "user", text: userInput }]);
    const currentInput = userInput;
    setUserInput("");
    setTranscript("");
    handleAIResponse(currentInput);
  };
  const startListening = () => {
    if (recognitionRef.current && !isListening && !isSpeaking) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };
  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      setIsListening(false);
      recognitionRef.current.stop();
      
      // Add any interim transcript to the input
      if (transcript) {
        setUserInput(prevInput => prevInput + transcript);
        setTranscript("");
      }
    }
  };
  // rest is ui related
  return (
    <div className="flex flex-col h-full bg-[#171717] text-white overflow-hidden">
      <div className="bg-[#1e1e1e] p-3 border-b border-gray-700 flex justify-between items-center">
        <h2 className="font-bold text-lg">{domain} Interview</h2>
        <div className="text-sm text-gray-400">
          Questions: {Math.floor(messages.length / 2)}
        </div>
      </div>
      
      <div 
        ref={messagesContainerRef}
        className="flex-grow overflow-y-auto p-4 bg-[#1e1e1e]"
        style={{ maxHeight: "calc(100% - 130px)" }}
      >
        <div className="space-y-4">
          {messages.map((msg, index) => (
            <div key={index} className={`${msg.sender === "ai" ? "bg-[#2a2a2a]" : "bg-[#333333]"} p-4 rounded-lg mb-4`}>
              <div className="flex items-center mb-2">
                <div className={`w-8 h-8 rounded-full ${msg.sender === "ai" ? "bg-blue-600" : "bg-green-600"} flex items-center justify-center mr-2`}>
                  <span className="text-sm font-bold">{msg.sender === "ai" ? "AI" : "You"}</span>
                </div>
                <span className="font-medium">{msg.sender === "ai" ? "AI Interviewer" : "You"}</span>
              </div>
              <p className="text-gray-200">{msg.text}</p>
            </div>
          ))}
          {isTyping && (
            <div className="bg-[#2a2a2a] p-4 rounded-lg">
              <div className="flex items-center mb-2">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center mr-2">
                  <span className="text-sm font-bold">AI</span>
                </div>
                <span className="font-medium">AI Interviewer</span>
              </div>
              <p className="text-gray-400">Thinking...</p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <div className="p-4 bg-[#1e1e1e] border-t border-gray-700">
        <form onSubmit={handleSendMessage}>
          <div className="mb-2">
            {transcript && (
              <div className="text-gray-400 text-sm italic mb-2">Hearing: {transcript}</div>
            )}
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={startListening}
                disabled={isListening || isSpeaking}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition duration-300 focus:outline-none disabled:opacity-50"
              >
                Start Speaking
              </button>
              <button
                type="button"
                onClick={stopListening}
                disabled={!isListening || isSpeaking}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition duration-300 focus:outline-none disabled:opacity-50"
              >
                Stop Speaking
              </button>
            </div>
          </div>
          <div className="flex">
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              className="flex-grow p-3 border border-gray-700 bg-[#2a2a2a] text-white focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-l"
              placeholder="Type your response or use speech buttons..."
            />
            <button 
              type="submit"
              className="bg-blue-600 text-white px-6 py-3 rounded-r hover:bg-blue-700 transition duration-300 focus:outline-none"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
export default ChatInterface;

// -----------------------------------------------

