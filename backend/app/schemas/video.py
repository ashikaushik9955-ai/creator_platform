from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class VideoResponse(BaseModel):
    id: int
    title: str
    description: str | None = None

    file_name: str
    file_size: int
    content_type: str
    status: Literal["processing", "completed", "failed"]

    low_file_path: str | None = Field(default=None, exclude=True)
    medium_file_path: str | None = Field(default=None, exclude=True)
    high_file_path: str | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def file_size_display(self) -> str:
        value = self.file_size

        if value < 1024:
            return f"{value} B"
        if value < 1024 ** 2:
            return f"{value / 1024:.2f} KB"
        if value < 1024 ** 3:
            return f"{value / (1024 ** 2):.2f} MB"
        return f"{value / (1024 ** 3):.2f} GB"


    @computed_field
    @property
    def low_url(self) -> str | None:
        return f"/media/{self.low_file_path}" if self.low_file_path else None

    @computed_field
    @property
    def medium_url(self) -> str | None:
        return f"/media/{self.medium_file_path}" if self.medium_file_path else None

    @computed_field
    @property
    def high_url(self) -> str | None:
        return f"/media/{self.high_file_path}" if self.high_file_path else None


class VideoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def title_cannot_be_null(cls, v):
        if v is None:
            raise ValueError("title cannot be null")
        return v