from pydantic import BaseModel, Field

class FigureDescription(BaseModel):

    description: str = Field(description="description of the image")

class ExpectedFigureDescription(BaseModel):
    description: str = Field(description="expected figure description")
