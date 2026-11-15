from pydantic import BaseModel , ConfigDict , Field, field_validator , computed_field



class VideoCreate(BaseModel):
    title: str
    description: str


class VideoResponse(BaseModel):

    id: int
    title: str
    description: str | None = None

    file_name: str | None = None
    file_size: int | None = None
    content_type: str | None = None
    status: str | None = None


    @computed_field
    @property

    def file_size_display(self) -> str | None:
        value = self.file_size

        if value is None:
            return None
        if value < 1024:
            return f"{value} B"
        if value < 1024 ** 2:
            return f"{value / 1024:.2f} KB"
        if value < 1024 ** 3:
            return f"{value / (1024 ** 2):.2f} MB"
        return f"{value / (1024 ** 3):.2f} GB"


class VideoUpdate(BaseModel):


    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None    


    @field_validator("title")
    @classmethod

    def title_cannot_be_null(cls, v):
        if v is None:
            raise ValueError("title cannot be null")

        return v
