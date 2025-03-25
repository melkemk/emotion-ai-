'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import * as Slider from '@radix-ui/react-slider';
import { ChatBubble } from './ChatBubble';

interface Message {
  content: string;
  isUser: boolean;
  anger: number;
  sadness: number;
  joy: number;
}

export default function ChatPage() {
  const [valence, setValence] = useState<number>(4);
  const [arousal, setArousal] = useState<number>(4);
  const [selectionThreshold, setSelectionThreshold] = useState<number>(4);
  const [resolutionLevel, setResolutionLevel] = useState<number>(4);
  const [goalDirectedness, setGoalDirectedness] = useState<number>(4);
  const [securingRate, setSecuringRate] = useState<number>(4);
  const [message, setMessage] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<Message[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('chatHistory');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  const [loading, setLoading] = useState(false);
  const [currentEmotions, setCurrentEmotions] = useState<{ anger: number; sadness: number; joy: number }>({
    anger: 0,
    sadness: 0,
    joy: 0,
  });
  const [bookFile, setBookFile] = useState<File | null>(null);
  const [characters, setCharacters] = useState<{ id: number; name: string; traits: string }[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('characters');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('selectedCharacter');
    }
    return null;
  });

  const sliderProps = { min: 1, max: 7, step: 1 };

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    localStorage.setItem('characters', JSON.stringify(characters));
    localStorage.setItem('selectedCharacter', selectedCharacter || '');
  }, [chatHistory, characters, selectedCharacter]);

  const extractCharacters = async () => {
    if (!bookFile) {
      alert('Please upload a PDF book.');
      return;
    }
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', bookFile);
      formData.append('book_title', bookFile.name.split('.', 1)[0]);

      const response = await axios.post('http://127.0.0.1:5000/extract_characters', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setCharacters(response.data.characters.slice(1));
      setBookFile(null);
    } catch (error) {
      console.error('Error extracting characters:', error);
      alert('Failed to extract characters.');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!message.trim()) return;
    if (!selectedCharacter) {
      alert('Please select a character to chat with.');
      return;
    }

    setLoading(true);
    const newMessage = { content: message, isUser: true, anger: 0, sadness: 0, joy: 0 };
    setChatHistory((prev) => [...prev, newMessage]);

    try {
      const response = await axios.post('http://127.0.0.1:5000/chat', {
        message,
        valence,
        arousal,
        selection_threshold: selectionThreshold,
        resolution: resolutionLevel,
        goal_directedness: goalDirectedness,
        securing_rate: securingRate,
        user_id: '1', // Hardcoded for simplicity; consider dynamic user IDs
        character_id: selectedCharacter,
      });

      setChatHistory(response.data.history.map((msg: any) => ({
        content: msg.content,
        isUser: msg.is_user,
        anger: msg.anger || 0,
        sadness: msg.sadness || 0,
        joy: msg.joy || 0,
      })));
      setCurrentEmotions({
        anger: response.data.anger,
        sadness: response.data.sadness,
        joy: response.data.joy,
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
        {/* Book Upload and Character Selection */}
        <div className="bg-white rounded-lg p-6 shadow-md">
          <h2 className="text-xl font-bold mb-4 text-black">Book Upload (PDF)</h2>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setBookFile(e.target.files?.[0] || null)}
            disabled={loading}
            className="w-full p-2 border border-gray-300 rounded text-black"
          />
          <button
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            onClick={extractCharacters}
            disabled={loading || !bookFile}
          >
            Extract Characters
          </button>
          {characters.length > 0 && (
            <div className="mt-4">
              <h3 className="font-medium text-black">Select a Character:</h3>
              <select
                className="mt-2 w-full p-2 border border-gray-300 rounded text-black"
                value={selectedCharacter || ''}
                onChange={(e) => setSelectedCharacter(e.target.value)}
                disabled={loading}
              >
                <option value="">-- Select a character --</option>
                {characters.map((char) => (
                  <option key={char.id} value={char.id}>
                    {char.name} {char.traits}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Parameter Controls */}
        <div className="bg-white rounded-lg p-6 shadow-md grid grid-cols-1 md:grid-cols-2 gap-4">
          <SliderControl label="Valence" value={valence} onValueChange={setValence} {...sliderProps} />
          <SliderControl label="Arousal" value={arousal} onValueChange={setArousal} {...sliderProps} />
          <SliderControl label="Selection Threshold" value={selectionThreshold} onValueChange={setSelectionThreshold} {...sliderProps} />
          <SliderControl label="Resolution Level" value={resolutionLevel} onValueChange={setResolutionLevel} {...sliderProps} />
          <SliderControl label="Goal-Directedness" value={goalDirectedness} onValueChange={setGoalDirectedness} {...sliderProps} />
          <SliderControl label="Securing Rate" value={securingRate} onValueChange={setSecuringRate} {...sliderProps} />
        </div>

        {/* Emotion Indicators */}
        <div className="bg-white rounded-lg p-4 shadow-md flex gap-4">
          <div className="flex-1">
            <h3 className="text-red-600 font-medium text-black">Anger: {currentEmotions.anger.toFixed(1)}</h3>
            <div className="h-2 bg-red-100 rounded-full">
              <div
                className="h-full bg-red-500 rounded-full transition-all duration-300"
                style={{ width: `${(currentEmotions.anger / 5) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-blue-600 font-medium text-black">Sadness: {currentEmotions.sadness.toFixed(1)}</h3>
            <div className="h-2 bg-blue-100 rounded-full">
              <div
                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                style={{ width: `${(currentEmotions.sadness / 5) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-green-600 font-medium text-black">Joy: {currentEmotions.joy.toFixed(1)}</h3>
            <div className="h-2 bg-green-100 rounded-full">
              <div
                className="h-full bg-green-500 rounded-full transition-all duration-300"
                style={{ width: `${(currentEmotions.joy / 5) * 100}%` }}
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
                joy={msg.joy}
              />
            ))}
            {loading && <div className="text-gray-500 text-black">Thinking...</div>}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type your message..."
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
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
      <label className="text-sm font-medium text-gray-700 text-black">{label}</label>
      <span className="text-sm text-gray-500 text-black">{value}</span>
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