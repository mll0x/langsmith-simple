from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    provider: str
    model: str
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int = 1024
    project_name: str = "playground"
    stream: bool = True


class ModelInfo(BaseModel):
    name: str
    provider: str
