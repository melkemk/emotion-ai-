'use client'
import { useState, useEffect } from 'react';
import axios from 'axios';
import * as Slider from '@radix-ui/react-slider';
import { ChatBubble } from './ChatBubble';

interface Message {
  content: string;
  isUser: boolean;
  anger: number;
  sadness: number;
}

export default function ChatPage() {
  const [valence, setValence] = useState<number>(4);
  const [arousal, setArousal] = useState<number>(4);
  const [selectionThreshold, setSelectionThreshold] = useState<number>(4);
  const [resolutionLevel, setResolutionLevel] = useState<number>(4);
  const [goalDirectedness, setGoalDirectedness] = useState<number>(4);
  const [securingRate, setSecuringRate] = useState<number>(4);
  const [message, setMessage] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentEmotions, setCurrentEmotions] = useState<{ anger: number; sadness: number }>({
    anger: 0,
    sadness: 0,
  });

  const sliderProps = {
    min: 1,
    max: 7,
    step: 1,
  };

  const sendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);

    const newMessage = { content: message, isUser: true, anger: 0, sadness: 0 };
    const updatedChatHistory = [...chatHistory, newMessage];

    try {
      console.log('Sending message:', message);
      const response = await axios.post('https://melkamumk.pythonanywhere.com/chat', {
        message: message,
        valence,
        arousal,
        selection_threshold: selectionThreshold,
        resolution: resolutionLevel,
        goal_directedness: goalDirectedness,
        securing_rate: securingRate,
        user_id: '1'
      });

      setChatHistory(prev => [
        ...prev,
        newMessage,
        { 
          content: response.data.message, 
          isUser: false,
          anger: response.data.anger,
          sadness: response.data.sadness
        }
      ]);
      
      setCurrentEmotions({
        anger: response.data.anger,
        sadness: response.data.sadness
      });
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 flex flex-col">
      <div className="max-w-4xl w-full mx-auto flex-1 flex flex-col gap-4">
        {/* Parameter Controls */}
        <div className="bg-white rounded-lg p-6 shadow-md grid grid-cols-1 md:grid-cols-2 gap-4">
          <SliderControl 
            label="Valence" 
            value={valence} 
            onValueChange={setValence}
            {...sliderProps}
          />
          <SliderControl 
            label="Arousal" 
            value={arousal} 
            onValueChange={setArousal}
            {...sliderProps}
          />
          <SliderControl 
            label="Selection Threshold" 
            value={selectionThreshold} 
            onValueChange={setSelectionThreshold}
            {...sliderProps}
          />
          <SliderControl 
            label="Resolution Level" 
            value={resolutionLevel} 
            onValueChange={setResolutionLevel}
            {...sliderProps}
          />
          <SliderControl 
            label="Goal-Directedness" 
            value={goalDirectedness} 
            onValueChange={setGoalDirectedness}
            {...sliderProps}
          />
          <SliderControl 
            label="Securing Rate" 
            value={securingRate} 
            onValueChange={setSecuringRate}
            {...sliderProps}
          />
        </div>

        {/* Emotion Indicators */}
        <div className="bg-white rounded-lg p-4 shadow-md flex gap-4">
          <div className="flex-1">
            <h3 className="text-red-600 font-medium">Anger: {currentEmotions.anger.toFixed(1)}</h3>
            <div className="h-2 bg-red-100 rounded-full">
              <div 
                className="h-full bg-red-500 rounded-full transition-all duration-300"
                style={{ width: `${(currentEmotions.anger / 5) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-blue-600 font-medium">Sadness: {currentEmotions.sadness.toFixed(1)}</h3>
            <div className="h-2 bg-blue-100 rounded-full">
              <div 
                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                style={{ width: `${(currentEmotions.sadness / 5) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="bg-white rounded-lg p-4 shadow-md flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto mb-4 space-y-4">
            {chatHistory.map((msg, index) => (
              <ChatBubble
                key={index}
                message={msg.content}
                isUser={msg.isUser}
                anger={msg.anger}
                sadness={msg.sadness}
              />
            ))}
            {loading && <div className="text-gray-500">Thinking...</div>}
          </div>

          {/* Input Area */}
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              className="flex-1 p-2 border rounded-lg"
              placeholder="Type your message..."
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const SliderControl = ({ label, value, onValueChange, min, max, step }: {
  label: string;
  value: number;
  onValueChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
}) => (
  <div className="space-y-2">
    <div className="flex justify-between">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <span className="text-sm text-gray-500">{value}</span>
    </div>
    <Slider.Root
      className="relative flex items-center h-5"
      value={[value]}
      onValueChange={([val]) => onValueChange(val)}
      min={min}
      max={max}
      step={step}
    >
      <Slider.Track className="bg-gray-200 relative flex-1 rounded-full h-2">
        <Slider.Range className="absolute bg-blue-600 rounded-full h-full" />
      </Slider.Track>
      <Slider.Thumb className="block w-5 h-5 bg-white rounded-full shadow-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </Slider.Root>
  </div>
);