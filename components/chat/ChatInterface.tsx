'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { apiClient, type ChatProvider } from '@/lib/api-client'

interface Message {
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [provider, setProvider] = useState<ChatProvider>('auto')

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return

        const userMessage: Message = {
            role: 'user',
            content: input,
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setInput('')
        setIsLoading(true)

        try {
            const data = await apiClient.sendChatMessage(input, provider)

            const assistantMessage: Message = {
                role: 'assistant',
                content: data.response || 'Sorry, I could not generate a response.',
                timestamp: new Date()
            }

            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            console.error('Chat error:', error)
            const errorMessage: Message = {
                role: 'assistant',
                content: `Error: Could not connect to backend (${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}).`,
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setIsLoading(false)
        }
    }

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    return (
        <div className="flex flex-col h-full bg-gradient-to-br from-gray-950 via-blue-950 to-gray-950">
            {/* Header */}
            <div className="glass-dark border-b border-white/10 p-4">
                <div className="flex items-center justify-between max-w-4xl mx-auto">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-ocean flex items-center justify-center shadow-glow">
                            <Bot className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-gradient">AI Ocean Assistant</h2>
                            <p className="text-xs text-gray-400">Ask me about ocean data, ARGO floats, or marine science</p>
                        </div>
                    </div>

                    {/* Provider Selector */}
                    <div className="flex gap-2">
                        <button
                            onClick={() => setProvider('auto')}
                            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${provider === 'auto'
                                    ? 'bg-gradient-ocean text-white shadow-glow'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                }`}
                        >
                            Auto
                        </button>
                        <button
                            onClick={() => setProvider('ollama')}
                            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${provider === 'ollama'
                                    ? 'bg-gradient-ocean text-white shadow-glow'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                }`}
                        >
                            Ollama
                        </button>
                        <button
                            onClick={() => setProvider('gemini')}
                            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${provider === 'gemini'
                                    ? 'bg-gradient-ocean text-white shadow-glow'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                }`}
                        >
                            Gemini
                        </button>
                        <button
                            onClick={() => setProvider('openai')}
                            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${provider === 'openai'
                                    ? 'bg-gradient-ocean text-white shadow-glow'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                }`}
                        >
                            OpenAI
                        </button>
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
                <div className="max-w-4xl mx-auto space-y-4">
                    {messages.length === 0 && (
                        <div className="text-center py-12">
                            <Sparkles className="w-12 h-12 mx-auto mb-4 text-ocean-400 opacity-50" />
                            <p className="text-gray-400 mb-2">Start a conversation</p>
                            <p className="text-sm text-gray-500">Ask about ARGO floats, ocean salinity, temperature data, or marine science</p>
                        </div>
                    )}

                    <AnimatePresence>
                        {messages.map((message, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                {message.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-lg bg-gradient-ocean flex items-center justify-center flex-shrink-0 shadow-glow">
                                        <Bot className="w-5 h-5" />
                                    </div>
                                )}

                                <div
                                    className={`max-w-[70%] rounded-2xl p-4 ${message.role === 'user'
                                            ? 'bg-gradient-ocean text-white shadow-glow'
                                            : 'glass-dark border border-white/10'
                                        }`}
                                >
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                                    <p className="text-xs opacity-50 mt-2">
                                        {message.timestamp.toLocaleTimeString()}
                                    </p>
                                </div>

                                {message.role === 'user' && (
                                    <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                                        <User className="w-5 h-5" />
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex gap-3"
                        >
                            <div className="w-8 h-8 rounded-lg bg-gradient-ocean flex items-center justify-center shadow-glow">
                                <Bot className="w-5 h-5" />
                            </div>
                            <div className="glass-dark border border-white/10 rounded-2xl p-4">
                                <Loader2 className="w-5 h-5 animate-spin text-ocean-400" />
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>

            {/* Input */}
            <div className="glass-dark border-t border-white/10 p-4">
                <div className="max-w-4xl mx-auto flex gap-3">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about ocean data, ARGO floats, or marine science..."
                        className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-ocean-400 resize-none"
                        rows={1}
                        disabled={isLoading}
                    />
                    <Button
                        onClick={sendMessage}
                        disabled={isLoading || !input.trim()}
                        className="bg-gradient-ocean hover:opacity-90 shadow-glow px-6"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </Button>
                </div>
            </div>
        </div>
    )
}
