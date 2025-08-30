from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from enum import Enum
import re
from datetime import datetime
from werkzeug.utils import secure_filename
import os

class ExperienceLevel(str, Enum):
    FRESHER = "Fresher"
    JUNIOR = "1-2 years"
    MID = "3-5 years"
    SENIOR = "5+ years"

class Domain(str, Enum):
    IT = "IT"
    HEALTHCARE = "Healthcare"
    MARKETING = "Marketing"
    FINANCE = "Finance"
    ENGINEERING = "Engineering"
    EDUCATION = "Education"

class Experience(BaseModel):
    job_title: str = Field(..., min_length=2, max_length=100)
    company: str = Field(..., min_length=2, max_length=100)
    duration: str = Field(..., pattern=r'^(Present|\d{4} - \d{4})$')
    description: str = Field(..., min_length=10, max_length=500)

    @validator('job_title')
    def sanitize_job_title(cls, v):
        return re.sub(r'[<>:"/\\|?*]', '', v).strip()

    @validator('description')
    def sanitize_description(cls, v):
        return re.sub(r'[<>:"/\\|?*]', '', v).strip()

class Education(BaseModel):
    degree: str = Field(..., min_length=2, max_length=100)
    institution: str = Field(..., min_length=2, max_length=100)
    graduation_year: int = Field(..., ge=1900, le=datetime.now().year)

    @validator('degree', 'institution')
    def sanitize_fields(cls, v):
        return re.sub(r'[<>:"/\\|?*]', '', v).strip()

class UserData(BaseModel):
    name: str = Field(
        default="User",
        min_length=2,
        max_length=50,
        pattern=r'^[a-zA-Z\s\-\'\.]*$',
        example="John Doe"
    )
    email: EmailStr = Field(
        default="user@example.com",
        example="john.doe@example.com"
    )
    phone: str = Field(
        default="+1234567890",
        pattern=r'^\+?[1-9]\d{1,14}$',
        example="+1234567890"
    )
    domain: Domain = Field(default=Domain.IT)
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.FRESHER)
    experiences: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(
        default_factory=list,
        min_items=0,
        max_items=15,
        example=["Python", "Project Management"]
    )
    certifications: List[str] = Field(default_factory=list)
    photo_url: Optional[str] = None

    @validator('name', pre=True, always=True)
    def default_name(cls, v):
        # If no name is provided or empty, use "User"
        if not v or v.strip() == "":
            return "User"
        return v

    @validator('name')
    def sanitize_name(cls, v):
        sanitized = re.sub(r'[^a-zA-Z\s\-\'\.]', '', v).strip()
        return ' '.join(word.capitalize() for word in sanitized.split())

    @validator('photo_url', pre=True)
    def secure_photo_filename(cls, v):
        if v:
            secure_name = secure_filename(os.path.basename(v))
            return f"/uploads/{secure_name}"
        return v

    @validator('skills', each_item=True)
    def sanitize_skill(cls, v):
        sanitized = re.sub(r'[<>:"/\\|?*]', '', v).strip()
        return sanitized[:50] if sanitized else None

    @validator('certifications', each_item=True)
    def sanitize_certification(cls, v):
        sanitized = re.sub(r'[<>:"/\\|?*]', '', v).strip()
        return sanitized[:100] if sanitized else None

    @validator('email')
    def validate_email_domain(cls, v):
        if not v:
            return "user@example.com"
        domain = v.split('@')[1].lower()
        if domain == "example.com":
            return v
        return v

    class Config:
        use_enum_values = True
        str_strip_whitespace = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        validate_assignment = True
        extra = "forbid"

class SecureUserResponse(UserData):
    class Config:
        exclude = {'phone', 'email'}

class ChatResponse(BaseModel):
    text: str
    options: List[str] = Field(default_factory=list)
    completed: bool = Field(default=False)
    current_field: Optional[str] = None
    security_token: Optional[str] = None
    error: Optional[str] = None

    class Config:
        str_strip_whitespace = True
        extra = "forbid"