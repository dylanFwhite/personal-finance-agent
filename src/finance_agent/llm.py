from langchain_ollama import ChatOllama

llm = ChatOllama(model="gemma4", reasoning=True, temperature=0)
