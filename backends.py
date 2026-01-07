# The Whetstone - Backend Abstraction Layer
# Supports both Ollama and llama-cpp-python backends

import os
import abc
import logging
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


class LLMBackend(abc.ABC):
    """Abstract base class for LLM backends."""
    
    @abc.abstractmethod
    def generate(self, prompt: str, stream: bool = True) -> Iterator[str]:
        """Generate a response from the LLM.
        
        Args:
            prompt: The full prompt to send to the model
            stream: If True, yield tokens as they're generated
            
        Yields:
            Token strings as they're generated
        """
        pass
    
    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available and ready."""
        pass
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of this backend."""
        pass


class OllamaBackend(LLMBackend):
    """Ollama API backend using OpenAI-compatible interface."""
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434/v1"):
        self.model = model
        self.base_url = base_url
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url, api_key="ollama")
        return self._client
    
    def generate(self, prompt: str, stream: bool = True) -> Iterator[str]:
        try:
            logger.debug(f"Sending request to Ollama: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
            )
        except Exception as e:
            logger.exception("Ollama request failed")
            # If streaming was requested, return an empty iterator so callers can handle gracefully
            if stream:
                return
            raise

        if stream:
            for chunk in response:
                logger.debug(f"Raw chunk: {chunk}")
                content = None
                # Try attribute-style access (OpenAI SDK object)
                try:
                    content = getattr(chunk.choices[0].delta, "content", None)
                except Exception:
                    pass

                # Try dict-like access
                if not content:
                    try:
                        if isinstance(chunk, dict):
                            choices = chunk.get("choices")
                            if choices and isinstance(choices[0], dict):
                                delta = choices[0].get("delta")
                                if isinstance(delta, dict):
                                    content = delta.get("content") or delta.get("text")
                                else:
                                    content = getattr(delta, "content", None)
                    except Exception:
                        pass

                # Fallbacks
                if not content:
                    try:
                        if isinstance(chunk, dict):
                             content = chunk.get("choices")[0].get("text")
                    except: pass

                if content:
                    logger.debug(f"Yielding content: {content!r}")
                    yield content
                else:
                    # ignore heartbeats/empty chunks
                    continue
        else:
            # Non-streaming
            text = None
            try:
                text = getattr(response.choices[0].message, "content", None)
            except Exception:
                pass
            if text:
                yield text
    
    def is_available(self) -> bool:
        import socket
        try:
            host = self.base_url.replace("http://", "").replace("/v1", "")
            if ":" in host:
                host, port = host.split(":")
                port = int(port)
            else:
                port = 11434
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            return False
    
    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"


class LlamaCppBackend(LLMBackend):
    """llama-cpp-python backend for direct model inference."""
    
    def __init__(self, model_path: str, n_ctx: int = 32768, n_gpu_layers: int = -1):
        """
        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU (-1 = all)
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._llm = None
    
    @property
    def llm(self):
        if self._llm is None:
            try:
                from llama_cpp import Llama
                logger.info(f"Loading model from {self.model_path}...")
                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    verbose=False,
                )
                logger.info("Model loaded successfully.")
            except ImportError:
                raise ImportError(
                    "llama-cpp-python is not installed. "
                    "Install with: pip install llama-cpp-python"
                )
        return self._llm
    
    def generate(self, prompt: str, stream: bool = True) -> Iterator[str]:
        if stream:
            response = self.llm(
                prompt,
                max_tokens=2048,
                stop=["User:", "\nUser"],
                stream=True,
            )
            for chunk in response:
                token = chunk["choices"][0]["text"]
                if token:
                    yield token
        else:
            response = self.llm(
                prompt,
                max_tokens=2048,
                stop=["User:", "\nUser"],
            )
            yield response["choices"][0]["text"]
    
    def is_available(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        try:
            from llama_cpp import Llama
            return True
        except ImportError:
            return False
    
    @property
    def name(self) -> str:
        return f"llama.cpp ({os.path.basename(self.model_path)})"


def create_backend(
    backend_type: Optional[str] = None,
    model: Optional[str] = None,
    model_path: Optional[str] = None,
) -> LLMBackend:
    """
    Factory function to create the appropriate backend.
    
    Environment variables:
        WHETSTONE_BACKEND: "ollama" (default) or "llamacpp"
        WHETSTONE_MODEL: Model name for Ollama (default: qwen3:14b)
        WHETSTONE_MODEL_PATH: Path to GGUF file for llama.cpp
    
    Args:
        backend_type: Override WHETSTONE_BACKEND env var
        model: Override WHETSTONE_MODEL env var (Ollama)
        model_path: Override WHETSTONE_MODEL_PATH env var (llama.cpp)
    
    Returns:
        Configured LLMBackend instance
    """
    backend = backend_type or os.getenv("WHETSTONE_BACKEND", "ollama").lower()
    
    if backend == "ollama":
        model_name = model or os.getenv("WHETSTONE_MODEL", "cogito:8b")
        return OllamaBackend(model=model_name)
    
    elif backend in ("llamacpp", "llama.cpp", "llama-cpp"):
        path = model_path or os.getenv("WHETSTONE_MODEL_PATH")
        if not path:
            # Try to find a .gguf file in common locations
            search_paths = [
                os.path.expanduser("~/.cache/huggingface/hub"),
                os.path.expanduser("~/models"),
                "/models",
                "./models",
            ]
            for search_dir in search_paths:
                if os.path.exists(search_dir):
                    for root, dirs, files in os.walk(search_dir):
                        for f in files:
                            if f.endswith(".gguf"):
                                path = os.path.join(root, f)
                                logger.info(f"Auto-detected model: {path}")
                                break
                        if path:
                            break
                if path:
                    break
        
        if not path:
            raise ValueError(
                "WHETSTONE_MODEL_PATH environment variable must be set when using llama.cpp backend. "
                "Example: export WHETSTONE_MODEL_PATH=/path/to/model.gguf"
            )
        
        n_ctx = int(os.getenv("WHETSTONE_CONTEXT_LENGTH", "32768"))
        return LlamaCppBackend(model_path=path, n_ctx=n_ctx)
    
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'ollama' or 'llamacpp'")
