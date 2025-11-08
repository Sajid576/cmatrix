import type { NextRequest } from "next/server"

export const runtime = "edge"

// Toggle between Python backend and direct HuggingFace API
const USE_PYTHON_BACKEND = process.env.USE_PYTHON_BACKEND === "true"
const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000"

export async function POST(req: NextRequest) {
  try {
    const { message, history = [] } = await req.json()

    if (!message) {
      return new Response("Message is required", { status: 400 })
    }

    // Route to Python backend if enabled
    if (USE_PYTHON_BACKEND) {
      console.log("[v0] Routing to Python backend:", PYTHON_BACKEND_URL)

      const response = await fetch(`${PYTHON_BACKEND_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          history,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error("[v0] Python backend error:", response.status, errorText)
        return new Response(JSON.stringify({ error: `Backend error: ${errorText}` }), {
          status: response.status,
          headers: { "Content-Type": "application/json" },
        })
      }

      // Forward the streaming response
      return new Response(response.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      })
    }

    // Original HuggingFace direct API call
    const API_KEY = process.env.HUGGINGFACE_API_KEY

    if (!API_KEY) {
      console.error("[v0] API key not found")
      return new Response("API key not configured", { status: 500 })
    }

    const messages: Array<{ role: "system" | "user" | "assistant"; content: string }> = [
      {
        role: "system",
        content:
          "You are DeepHat, created by Kindo.ai. You are a helpful assistant that is an expert in Cybersecurity and DevOps.",
      },
      ...history,
      { role: "user", content: message },
    ]

    console.log("[v0] Sending request to Hugging Face with", messages.length, "messages")

    const response = await fetch("https://router.huggingface.co/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${API_KEY}`,
      },
      body: JSON.stringify({
        model: "DeepHat/DeepHat-V1-7B:featherless-ai",
        messages: messages,
        max_tokens: 512,
        temperature: 0.7,
        top_p: 0.95,
        stream: true,
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("[v0] Hugging Face API error:", response.status, errorText)
      return new Response(JSON.stringify({ error: `API error: ${errorText}` }), {
        status: response.status,
        headers: { "Content-Type": "application/json" },
      })
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    const encoder = new TextEncoder()

    if (!reader) {
      return new Response(JSON.stringify({ error: "No response body" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      })
    }

    const readableStream = new ReadableStream({
      async start(controller) {
        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value, { stream: true })
            const lines = chunk.split("\n").filter((line) => line.trim() !== "")

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const data = line.slice(6)
                if (data === "[DONE]") {
                  controller.enqueue(encoder.encode("data: [DONE]\n\n"))
                  continue
                }

                try {
                  const json = JSON.parse(data)
                  const content = json.choices?.[0]?.delta?.content
                  if (content) {
                    controller.enqueue(encoder.encode(`data: ${JSON.stringify({ token: content })}\n\n`))
                  }
                } catch (e) {
                  // Skip invalid JSON
                }
              }
            }
          }
        } catch (error) {
          console.error("[v0] Streaming error:", error)
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ error: "Stream interrupted" })}\n\n`))
        } finally {
          controller.close()
        }
      },
    })

    return new Response(readableStream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    })
  } catch (error: any) {
    console.error("[v0] Error in chat route:", error?.message)
    return new Response(JSON.stringify({ error: "Internal server error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    })
  }
}
