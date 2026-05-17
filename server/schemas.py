from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


NodeStatus = Literal["pending", "running", "done", "error"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class MdxOutput(BaseModel):
    topic: str
    mdx: str
    status: str
    cloudinary_image_urls: list[str] = Field(default_factory=list)


class GenerationRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topics: list[str]
    mdx_outputs: list[MdxOutput]
    overall_status: str
    created_at: datetime
    completed_at: datetime | None


class GenerateRequest(BaseModel):
    topics_raw: str


class NodeEvent(BaseModel):
    node: str
    status: NodeStatus
    message: str
    elapsed_ms: int
    topic: str
