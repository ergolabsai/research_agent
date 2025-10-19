from pydantic import BaseModel, Field

class FigureDescription(BaseModel):

    name: str = Field(description="name of the image")
    description: str = Field(description="description of the image")

