from pydantic import BaseModel, Field


class FreezeAccountRequest(BaseModel):
    reason: str = Field(default="Risk score exceeded threshold")
    performed_by: str = Field(default="analyst")


class TransactionRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
