from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)


class AuthUser(BaseModel):
    id: int
    name: str
    email: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str


class AuthResponse(BaseModel):
    user: AuthUser
    tokens: AuthTokens | None = None


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None


class LogoutResponse(BaseModel):
    detail: str = "logged_out"
