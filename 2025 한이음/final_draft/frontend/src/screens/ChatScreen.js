import React, { useState } from 'react';
import ChatHeader from '../components/ChatHeader';
import MessageList from '../components/MessageList';
import ChatInput from '../components/ChatInput';
import '../styles/ChatScreen.css'; // 수정된 경로

function ChatScreen() {
  // 실제 대화 데이터를 저장할 state
  const [messages, setMessages] = useState([
    { sender: 'bot', text: '네, 대화 준비가 완료되었습니다. 어떤 도움이 필요하신가요?' },
  ]);

  // 사용자가 메시지를 보냈을 때 처리하는 함수
  const handleSendMessage = (newMessageText) => {
    // 사용자 메시지 추가
    const newUserMessage = { sender: 'user', text: newMessageText };
    
    // 봇의 응답 (지금은 간단한 메아리로 구현)
    // TODO: 추후에 AI 응답 로직으로 교체해야 합니다.
    const botResponse = { sender: 'bot', text: `"${newMessageText}" 라고 말씀하셨네요!` };

    // 메시지 목록 업데이트
    setMessages(prevMessages => [...prevMessages, newUserMessage, botResponse]);
  };

  return (
    <div className="chat-screen">
      <ChatHeader />
      <MessageList messages={messages} />
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

export default ChatScreen;