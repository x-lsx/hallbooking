from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(...,
                            description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(...,
                                    description="Refresh token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "jwt...",
                "refresh_token": "jwt...",
                "token_type": "bearer",
                "expires_in": 900,
                "refresh_expires_in": 604800,
            }
        }
    )


class AccessTokenPayload(BaseModel):
    sub: str = Field(..., description="User ID")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at time (Unix timestamp)")
    type: str = Field(default="access", description="Token type")


class RefreshTokenPayload(BaseModel):
    sub: str = Field(..., description="User ID")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at time (Unix timestamp)")
    jti: str = Field(...,
                     description="JWT ID (unique identifier for the token)")
    type: str = Field(default="refresh", description="Token type")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT refresh token")
