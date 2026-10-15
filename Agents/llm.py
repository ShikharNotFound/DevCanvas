import os
from abc import ABC,abstractmethod
from dotenv import load_dotenv

load_dotenv()


class LLMClient(ABC):
    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.2,
        json_mode: bool = False,
    )-> str : 
        ...



class OpenAICompatibilityClient(LLMClient):
    def __init__(self,base_url: str, api_key : str ,model: str):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(base_url = base_url, api_key = api_key)
        self._model = model

    async def complete(self, system, user, temperature=0.2, json_mode=False):
        kwargs = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content



class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str, max_tokens: int = 8192):
        from anthropic import AsyncAnthropic
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    async def complete(self, system, user, temperature=0.2, json_mode=False):
        resp = await self._client.messages.create(
            model=self._model,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=self._max_tokens,
        )
        return resp.content[0].text



class EchoClient(LLMClient) :
    async def complete(self, system, user, temperature=0.2, json_mode=False):
        preview = user[:120].replace("\n"," ")

        if json_mode :
            return '{"files" : [], "summary" : "Echo client - no real LLM used. "}'
        return f"[Echo] system_len = {len(system)} user_review = {preview!r}"






def get_llm(role : str = "default") -> LLMClient :
    role_key = role.upper()

    provider = (
        os.getenv(f"{role_key}_PROVIDER")
        or os.getenv("LLM_PROVIDER","groq")
    )
    

    model = (
        os.getenv(f"{role_key}_MODEL")
        or os.getenv("LLM_MODEL")
    )


    if provider == "echo" : 
        return EchoClient()


    if provider == "groq" :
        return OpenAICompatibilityClient(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY", ""),
            model=model or "openai/gpt-oss-120b",
        )

    if provider == "openai" :
         return OpenAICompatibilityClient(
            base_url="https://api.openai.com/v1",
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=model or "gpt-4o-mini",
        )


    if provider == "anthropic":
        return AnthropicClient(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=model or "claude-sonnet-4-5",
        )
    
    if provider == "gemini":
        return OpenAICompatibilityClient(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=model or "gemini-3.8-flash",
        )

    if provider == "ollama":
        return OpenAICompatibilityClient(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model=model or "qwen2.5-coder:7b",
        )

    raise ValueError(
        f"Unknown provider '{provider}'. "
        f"Supported: groq, openai, anthropic, ollama, echo."
    )