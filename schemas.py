from pydantic import BaseModel, Field

class StudentCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    level: str = Field(pattern="^(primaria|bachillerato)$")
    grade: str | None = Field(default=None, max_length=20)
    lichess_username: str = Field(min_length=2, max_length=60)

class StudentOut(BaseModel):
    id: int
    full_name: str
    level: str
    grade: str | None
    lichess_username: str

    class Config:
        from_attributes = True
