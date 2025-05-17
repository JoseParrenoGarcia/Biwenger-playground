import os
import tomllib

from langchain.chat_models import ChatOpenAI

# Load TOML
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
secrets_path = os.path.join(root_dir, "secrets", "openAI.toml")

with open(secrets_path, "rb") as f:
    config = tomllib.load(f)

api_key = config["openai"]["api_key"]
model = config["openai"].get("model", "gpt-3.5-turbo")

# Create LLM client
llm = ChatOpenAI(
    openai_api_key=api_key,
    model=model,
    temperature=0.0,
    max_tokens=500,
    request_timeout=30
)