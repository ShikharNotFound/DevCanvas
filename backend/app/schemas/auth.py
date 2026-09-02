from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str | None = None




class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str




class UserLogin(BaseModel):
    email: EmailStr
    password: str



class User(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str