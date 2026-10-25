# ShopTrack AI Maintenance Assistant
# MS628 - Final Project
# Flask application connected to a local Ollama Llama model.

import json
import os
from urllib import request, error

from flask import Flask, jsonify, render_template, request as flask_request


# Create the Flask web application.
app = Flask(__name__)


# Ollama normally runs directly on this computer.
#
# When ShopTrack later runs inside Docker, we can provide
# a different OLLAMA_URL environment variable so the
# container can communicate with Ollama on the host computer.
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)


# Local AI model used by ShopTrack.
MODEL = "llama3.2:1b"


@app.get("/")
def home():
    """Display the ShopTrack web interface."""

    return render_template("index.html")


@app.post("/api/chat")
def chat():
    """Receive a maintenance question and return a local AI response."""

    # Read the information sent from the browser.
    data = flask_request.get_json(silent=True) or {}

    question = data.get("question", "")
    history = data.get("history", [])


    # Make sure the user entered a valid question.
    if not isinstance(question, str) or not question.strip():

        return jsonify({
            "error": "Please enter a question."
        }), 400


    # Prevent extremely large questions from being submitted.
    if len(question) > 2000:

        return jsonify({
            "error": "The question is too long."
        }), 400


    # Build a safe version of this browser's conversation history.
    safe_history = []


    if isinstance(history, list):

        for message in history[-10:]:

            if not isinstance(message, dict):
                continue


            role = message.get("role")
            content = message.get("content")


            if (
                role in ("user", "assistant")
                and isinstance(content, str)
            ):

                safe_history.append({
                    "role": role,
                    "content": content[:4000]
                })


    # Give the local AI its purpose and response guidelines.
    messages = [
        {
            "role": "system",

            "content": (
                "You are ShopTrack AI, a local equipment maintenance "
                "and troubleshooting assistant. Give clear, practical, "
                "educational answers that are easy to understand. "
                "Use plain text only. Do not use Markdown formatting, "
                "asterisks, hashtags, or Markdown tables. "
                "When giving steps, use simple numbered lists. "
                "Keep answers organized and focused on the user's question. "
                "Always remind users to follow manufacturer instructions, "
                "lockout/tagout requirements when applicable, and workplace "
                "safety procedures."
            )
        }
    ]


    # Add the current browser's previous conversation.
    messages.extend(safe_history)


    # Add the user's newest question.
    messages.append({
        "role": "user",
        "content": question.strip()
    })


    # Convert the conversation into JSON for Ollama.
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": False
    }).encode("utf-8")


    try:

        # Send the question to the locally running Ollama service.
        ollama_request = request.Request(
            OLLAMA_URL,
            data=payload,
            headers={
                "Content-Type": "application/json"
            }
        )


        # Wait for Ollama to return the AI-generated answer.
        with request.urlopen(
            ollama_request,
            timeout=120
        ) as response:

            result = json.load(response)


        # Get the AI response.
        answer = result["message"]["content"]


        # Remove Markdown-style symbols so the browser
        # displays cleaner plain text.
        answer = answer.replace("\\*\\*", "")
        answer = answer.replace("**", "")
        answer = answer.replace("\\*", "")


        # Send the cleaned response back to the browser.
        return jsonify({
            "answer": answer
        })


    except (error.URLError, TimeoutError):

        return jsonify({
            "error": "Ollama is unavailable or took too long to respond."
        }), 503


    except (KeyError, ValueError):

        return jsonify({
            "error": "The AI returned an unexpected response."
        }), 502


if __name__ == "__main__":

    # Using 0.0.0.0 allows the Flask app to run
    # locally and inside a Docker container.
    #
    # Threading allows separate browser requests
    # to be handled independently.
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )