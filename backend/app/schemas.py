from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoutiqueRead(BaseModel):
    id: int
    name: str
    integration_type: str

    model_config = ConfigDict(from_attributes=True)


class ProductRead(BaseModel):
    id: int
    boutique_id: int
    boutique: str
    name: str
    description: str
    price: float
    currency: str
    stock_quantity: int


class SyncResult(BaseModel):
    boutique_id: int
    boutique: str
    received: int
    created: int
    updated: int
    message: str


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=99)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def product_ids_are_unique(self):
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Each product can only appear once in an order")
        return self


class OrderItemRead(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    quantity: int


class OrderRead(BaseModel):
    id: int
    total_amount: float
    currency: str
    created_at: datetime
    items: list[OrderItemRead]
