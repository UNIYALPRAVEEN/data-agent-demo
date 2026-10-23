"""
chatbot.py  -  the same question, sent to a plain chatbot.

No tools, no database. It has never seen your data, so all it can do is guess.
Compare it with agent.py, which can look at the tables and run SQL.

RUN IT
  python chatbot.py "Why did our orders drop in Mumbai last week?"
"""
import os
import sys

from anthropic import Anthropic

import show

QUESTION = sys.argv[1]
MODEL = os.environ.get("DATA_AGENT_MODEL", "claude-sonnet-5-5")

client = Anthropic()
response = client.messages.create(
    model=MODEL,
    max_tokens=500,
    system="You work at a food delivery company in India. Answer in one short paragraph.",
    messages=[{"role": "user", "content": QUESTION}],   # just the question. No tools, no data.
)
answer = "\n\n".join(block.text for block in response.content if block.type == "text")   # skip thinking blocks
show.chatbot(QUESTION, answer)
