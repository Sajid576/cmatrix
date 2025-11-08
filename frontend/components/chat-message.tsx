import { cn } from "@/lib/utils"
import { User, Sparkles, Loader2 } from "lucide-react"
import ReactMarkdown from "react-markdown"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  isLoading?: boolean
}

export function ChatMessage({ role, content, isLoading }: ChatMessageProps) {
  const isUser = role === "user"

  return (
    <div className={cn("flex gap-4 group", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="flex items-start flex-shrink-0">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-chart-1">
            <Sparkles className="w-4 h-4 text-primary-foreground" />
          </div>
        </div>
      )}

      <div className={cn("flex flex-col gap-2 max-w-[80%] sm:max-w-[70%]", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser ? "bg-primary text-primary-foreground" : "bg-muted text-foreground",
          )}
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-muted-foreground">Thinking...</span>
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {isUser ? content : <ReactMarkdown>{content || "\u00A0"}</ReactMarkdown>}
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex items-start flex-shrink-0">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-secondary">
            <User className="w-4 h-4 text-secondary-foreground" />
          </div>
        </div>
      )}
    </div>
  )
}
