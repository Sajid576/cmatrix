"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Loader2, Sparkles } from "lucide-react"
import { ChatMessage } from "@/components/chat-message"

export default function ChatPage() {
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput("")
    setMessages((prev) => [...prev, { role: "user", content: userMessage }])
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          history: messages.slice(-10), // Send last 10 messages for context
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }))
        throw new Error(errorData.error || "Failed to fetch")
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = ""

      // Add empty assistant message
      setMessages((prev) => [...prev, { role: "assistant", content: "" }])

      if (!reader) {
        throw new Error("No response body")
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split("\n").filter(line => line.trim() !== "")

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim()
            if (data === "[DONE]") continue

            try {
              const parsed = JSON.parse(data)
              if (parsed.token) {
                assistantMessage += parsed.token
                // Update the last message with accumulated content
                setMessages((prev) => {
                  const updated = [...prev]
                  updated[updated.length - 1] = {
                    role: "assistant",
                    content: assistantMessage
                  }
                  return updated
                })
              } else if (parsed.error) {
                console.error("[v0] Stream error:", parsed.error)
                throw new Error(parsed.error)
              }
            } catch (e) {
              if (e instanceof Error && e.message !== "Unexpected end of JSON input") {
                console.error("[v0] Parse error:", e)
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("[v0] Error:", error)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}. Please try again.`,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container flex items-center justify-between h-14 px-4 mx-auto">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-chart-1">
              <Sparkles className="w-4 h-4 text-primary-foreground" />
            </div>
            <h1 className="text-lg font-semibold">DeepHat AI Chat</h1>
          </div>
          <div className="text-xs text-muted-foreground">Powered by DeepHat-V1-7B</div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="container max-w-4xl px-4 py-8 mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-8 py-12">
              <div className="flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-chart-1">
                <Sparkles className="w-10 h-10 text-primary-foreground" />
              </div>
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-balance">Welcome to DeepHat AI</h2>
                <p className="text-muted-foreground text-pretty max-w-md">
                  Start a conversation with DeepHat-V1-7B. Ask questions, get insights, or just chat!
                </p>
              </div>
              <div className="grid gap-3 mt-4 sm:grid-cols-2">
                <button
                  onClick={() => setInput("What are your capabilities?")}
                  className="px-4 py-3 text-sm text-left transition-colors border rounded-lg border-border hover:bg-accent hover:text-accent-foreground"
                >
                  <div className="font-medium">What are your capabilities?</div>
                  <div className="text-xs text-muted-foreground">Learn what I can do</div>
                </button>
                <button
                  onClick={() => setInput("Tell me an interesting fact")}
                  className="px-4 py-3 text-sm text-left transition-colors border rounded-lg border-border hover:bg-accent hover:text-accent-foreground"
                >
                  <div className="font-medium">Tell me an interesting fact</div>
                  <div className="text-xs text-muted-foreground">Discover something new</div>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message, index) => (
                <ChatMessage key={index} role={message.role} content={message.content} />
              ))}
              {isLoading && messages[messages.length - 1]?.role === "user" && (
                <ChatMessage role="assistant" content="" isLoading />
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-card">
        <div className="container max-w-4xl px-4 py-4 mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message DeepHat AI..."
              className="pr-12 resize-none min-h-[60px] max-h-[200px]"
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isLoading}
              className="absolute bottom-2 right-2 rounded-lg"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </form>
          <p className="mt-2 text-xs text-center text-muted-foreground">
            AI responses may not always be accurate. Verify important information.
          </p>
        </div>
      </div>
    </div>
  )
}
