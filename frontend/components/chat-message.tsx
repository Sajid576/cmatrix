import { cn } from "@/lib/utils"
import { User, Shield, Loader2 } from "lucide-react"
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
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-secondary cyber-border">
            <Shield className="w-5 h-5 text-secondary-foreground" />
          </div>
        </div>
      )}

      <div className={cn("flex flex-col gap-2 max-w-[80%] sm:max-w-[70%]", isUser && "items-end")}>
        {!isUser && (
          <div className="text-xs text-muted-foreground terminal-text flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
            DEEPHAT AGENT
          </div>
        )}
        <div
          className={cn(
            "rounded-lg px-4 py-3 text-sm leading-relaxed cyber-border",
            isUser
              ? "bg-black text-white"
              : "bg-muted text-foreground terminal-text",
            !isUser && "scan-line"
          )}
        >
          {isLoading ? (
            <div className="flex items-center gap-2 terminal-text">
              <Loader2 className="w-4 h-4 animate-spin text-green-400" />
              <span className="text-muted-foreground">[PROCESSING QUERY...]</span>
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {isUser ? (
                <span>{content}</span>
              ) : (
                <ReactMarkdown>{content || "\u00A0"}</ReactMarkdown>
              )}
            </div>
          )}
        </div>
        {isUser && (
          <div className="text-xs text-muted-foreground terminal-text flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
            HUMAN OPERATOR
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex items-start flex-shrink-0">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-secondary cyber-border">
            <User className="w-5 h-5 text-secondary-foreground" />
          </div>
        </div>
      )}
    </div>
  )
}
