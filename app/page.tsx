"use client"
import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { ChatBubble } from "./ChatBubble"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Send, BookOpen, User, Brain, MessageSquare, Loader2 } from "lucide-react"

interface Message {
  content: string
  isUser: boolean
  anger: number
  sadness: number
  joy: number
}

interface Parameters {
  valence: number
  arousal: number
  selection_threshold: number
  resolution: number
  goal_directedness: number
  securing_rate: number
}

export default function ChatPage() {
  const [message, setMessage] = useState<string>("")
  const [chatHistory, setChatHistory] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [currentEmotions, setCurrentEmotions] = useState<{ anger: number; sadness: number; joy: number }>({
    anger: 0,
    sadness: 0,
    joy: 0,
  })
  const [currentParameters, setCurrentParameters] = useState<Parameters>({
    valence: 0,
    arousal: 0,
    selection_threshold: 0,
    resolution: 0,
    goal_directedness: 0,
    securing_rate: 0,
  })
  const [currentTraits, setCurrentTraits] = useState<string>("")
  const [bookFile, setBookFile] = useState<File | null>(null)
  const [characters, setCharacters] = useState<{ id: number; name: string; traits: string }[]>([])
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null)
  const [userId] = useState<string>("1") // Hardcoded for now
  const [activeTab, setActiveTab] = useState("chat")
  const [isDarkMode, setIsDarkMode] = useState(false)

  const chatContainerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Scroll to bottom of chat when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatHistory]) 

  // Toggle dark mode
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }, [isDarkMode])

  const extractCharacters = async () => {
    if (!bookFile) {
      alert("Please upload a PDF book.")
      return
    }
    try {
      setLoading(true)
      const formData = new FormData()
      formData.append("file", bookFile)
      formData.append("book_title", bookFile.name.split(".", 1)[0])

      const response = await axios.post("https://melkamumk.pythonanywhere.com/extract_characters", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      setCharacters(response.data.characters.slice(1))
      setBookFile(null)
      setActiveTab("characters")
    } catch (error) {
      console.error("Error extracting characters:", error)
      alert("Failed to extract characters.")
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async () => {
    if (!message.trim()) return
    if (!selectedCharacter) {
      alert("Please select a character to chat with.")
      setActiveTab("characters")
      return
    }

    setLoading(true)
    const newUserMessage = { content: message, isUser: true, anger: 0, sadness: 0, joy: 0 }
    const updatedHistory = [...chatHistory, newUserMessage]
    setChatHistory(updatedHistory)

    try {
      const response = await axios.post("https://melkamumk.pythonanywhere.com/chat", { 
        message,
        history: updatedHistory.map((msg) => ({ content: msg.content, is_user: msg.isUser })),
        user_id: userId,
        character_id: selectedCharacter,
      })

      const aiMessage = {
        content: response.data.message,
        isUser: false,
        anger: response.data.emotions.anger,
        sadness: response.data.emotions.sadness,
        joy: response.data.emotions.joy,
      }
      setChatHistory([...updatedHistory, aiMessage])
      setCurrentEmotions(response.data.emotions)
      setCurrentParameters(response.data.parameters)
      setCurrentTraits(response.data.traits)
      setMessage("")
    } catch (error) {
      console.error("Error sending message:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileButtonClick = () => {
    fileInputRef.current?.click()
  }

  const getSelectedCharacterName = () => {
    if (!selectedCharacter) return "No character selected"
    const character = characters.find((c) => c.id.toString() === selectedCharacter)
    return character ? character.name : "Unknown character"
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30 dark:from-background dark:to-background p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header with dark mode toggle */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            Character Chat AI
          </h1>
          <Button variant="outline" size="icon" onClick={() => setIsDarkMode(!isDarkMode)} className="rounded-full">
            {isDarkMode ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2" />
                <path d="M12 20v2" />
                <path d="m4.93 4.93 1.41 1.41" />
                <path d="m17.66 17.66 1.41 1.41" />
                <path d="M2 12h2" />
                <path d="M20 12h2" />
                <path d="m6.34 17.66-1.41 1.41" />
                <path d="m19.07 4.93-1.41 1.41" />
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
              </svg>
            )}
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chat and Controls */}
          <div className="lg:col-span-2 space-y-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid grid-cols-3 mb-4">
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  <span className="hidden sm:inline">Chat</span>
                </TabsTrigger>
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4" />
                  <span className="hidden sm:inline">Upload Book</span>
                </TabsTrigger>
                <TabsTrigger value="characters" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span className="hidden sm:inline">Characters</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="chat" className="mt-0">
                <Card className="border-none shadow-lg bg-card/80 backdrop-blur-sm">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex justify-between items-center">
                      <span>Chat with {getSelectedCharacterName()}</span>
                      {selectedCharacter && (
                        <div className="flex gap-2">
                          <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">
                            {characters.find((c) => c.id.toString() === selectedCharacter)?.traits.split(",")[0]}
                          </span>
                        </div>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div
                      ref={chatContainerRef}
                      className="h-[60vh] overflow-y-auto pr-2 space-y-4 scrollbar-thin scrollbar-thumb-primary/20 scrollbar-track-transparent"
                    >
                      {chatHistory.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                          <MessageSquare className="h-12 w-12 mb-4 opacity-20" />
                          <p>Select a character and start chatting</p>
                          <Button variant="link" onClick={() => setActiveTab("characters")} className="mt-2">
                            Choose a character
                          </Button>
                        </div>
                      )}

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

                      {loading && (
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Thinking...</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                  <CardFooter>
                    <div className="flex w-full gap-2">
                      <Input
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                        placeholder="Type your message..."
                        disabled={loading || !selectedCharacter}
                        className="flex-1"
                      />
                      <Button
                        onClick={sendMessage}
                        disabled={loading || !selectedCharacter || !message.trim()}
                        className="px-4"
                      >
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        <span className="ml-2 hidden sm:inline">Send</span>
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              </TabsContent>

              <TabsContent value="upload" className="mt-0">
                <Card className="border-none shadow-lg bg-card/80 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle>Upload Book (PDF)</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div
                      className="border-2 border-dashed border-muted-foreground/20 rounded-lg p-8 text-center cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={handleFileButtonClick}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setBookFile(e.target.files?.[0] || null)}
                        disabled={loading}
                        className="hidden"
                      />
                      <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                      <p className="text-muted-foreground mb-2">
                        {bookFile ? bookFile.name : "Drag & drop or click to upload a PDF book"}
                      </p>
                      {bookFile && (
                        <p className="text-xs text-muted-foreground">{(bookFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                      )}
                    </div>

                    <Button className="w-full" onClick={extractCharacters} disabled={loading || !bookFile}>
                      {loading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Extracting Characters...
                        </>
                      ) : (
                        <>
                          <BookOpen className="h-4 w-4 mr-2" />
                          Extract Characters
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="characters" className="mt-0">
                <Card className="border-none shadow-lg bg-card/80 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle>Select a Character</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {characters.length === 0 ? (
                      <div className="text-center py-8">
                        <User className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                        <p className="text-muted-foreground">No characters available</p>
                        <Button variant="link" onClick={() => setActiveTab("upload")} className="mt-2">
                          Upload a book to extract characters
                        </Button>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {characters.map((char) => (
                          <Card
                            key={char.id}
                            className={`cursor-pointer transition-all hover:shadow-md ${
                              selectedCharacter === char.id.toString() ? "border-primary bg-primary/5" : "border-border"
                            }`}
                            onClick={() => setSelectedCharacter(char.id.toString())}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                                  <User className="h-5 w-5 text-primary" />
                                </div>
                                <div>
                                  <h3 className="font-medium">{char.name}</h3>
                                  <p className="text-xs text-muted-foreground line-clamp-1">{char.traits}</p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                  </CardContent>
                  {selectedCharacter && (
                    <CardFooter>
                      <Button className="w-full" onClick={() => setActiveTab("chat")}>
                        <MessageSquare className="h-4 w-4 mr-2" />
                        Start Chatting
                      </Button>
                    </CardFooter>
                  )}
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar with Character Info and Emotions */}
          <div className="space-y-6">
            {/* Character Traits */}
            {currentTraits && (
              <Card className="border-none shadow-lg bg-card/80 backdrop-blur-sm">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Character Traits
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{currentTraits}</p>
                </CardContent>
              </Card>
            )}

            {/* Emotion Indicators */}
            <Card className="border-none shadow-lg bg-card/80 backdrop-blur-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Emotional State</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-red-500"></div>
                      <span className="text-sm font-medium">Anger</span>
                    </div>
                    <span className={`text-sm font-medium ${currentEmotions.anger > 3 ? "text-red-500" : ""}`}>
                      {currentEmotions.anger.toFixed(1)}
                    </span>
                  </div>
                  <Progress
                    value={(currentEmotions.anger / 5) * 100}
                    className="h-2 bg-red-100"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-blue-500"></div>
                      <span className="text-sm font-medium">Sadness</span>
                    </div>
                    <span className={`text-sm font-medium ${currentEmotions.sadness > 3 ? "text-blue-500" : ""}`}>
                      {currentEmotions.sadness.toFixed(1)}
                    </span>
                  </div>
                  <Progress
                    value={(currentEmotions.sadness / 5) * 100}
                    className="h-2 bg-blue-100"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-green-500"></div>
                      <span className="text-sm font-medium">Joy</span>
                    </div>
                    <span className={`text-sm font-medium ${currentEmotions.joy > 3 ? "text-green-500" : ""}`}>
                      {currentEmotions.joy.toFixed(1)}
                    </span>
                  </div>
                  <Progress
                    value={(currentEmotions.joy / 5) * 100}
                    className="h-2 bg-green-100"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Parameter Display */}
            <Card className="border-none shadow-lg bg-card/80 backdrop-blur-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Character Parameters</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ParameterDisplay label="Valence" value={currentParameters.valence} max={7} />
                <ParameterDisplay label="Arousal" value={currentParameters.arousal} max={7} />
                <ParameterDisplay label="Selection Threshold" value={currentParameters.selection_threshold} max={7} />
                <ParameterDisplay label="Resolution" value={currentParameters.resolution} max={7} />
                <ParameterDisplay label="Goal-Directedness" value={currentParameters.goal_directedness} max={7} />
                <ParameterDisplay label="Securing Rate" value={currentParameters.securing_rate} max={7} />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

const ParameterDisplay = ({ label, value, max }: { label: string; value: number; max: number }) => (
  <div className="space-y-2">
    <div className="flex justify-between items-center">
      <span className="text-sm font-medium">{label}</span>
      <span className="text-sm text-muted-foreground">{value.toFixed(1)}</span>
    </div>
    <Progress value={(value / max) * 100} className="h-2" />
  </div>
)

