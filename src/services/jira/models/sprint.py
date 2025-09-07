from pydantic import BaseModel, Field, AliasChoices
from pydantic.alias_generators import to_camel


class Sprint(BaseModel):
    id: int
    self: str | None = Field(default=None)
    state: str
    name: str
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    complete_date: str | None = Field(default=None, alias="completeDate")
    origin_board_id: int = Field(
        validation_alias=AliasChoices("boardId", "originBoardId")
    )
    goal: str

    class Config:
        alias_generator = to_camel
        validate_by_name = True
