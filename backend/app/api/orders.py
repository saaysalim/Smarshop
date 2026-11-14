from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Order, OrderItem, Product
from ..schemas import OrderCreate, OrderRead

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    quantities = {item.product_id: item.quantity for item in payload.items}
    products = db.scalars(
        select(Product)
        .where(Product.id.in_(quantities))
        .order_by(Product.id)
        .with_for_update()
    ).all()
    products_by_id = {product.id: product for product in products}

    missing_ids = sorted(set(quantities) - products_by_id.keys())
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found: {', '.join(map(str, missing_ids))}",
        )

    currencies = {products_by_id[product_id].currency for product_id in quantities}
    if len(currencies) != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Products in different currencies cannot be checked out together",
        )

    for product_id, quantity in quantities.items():
        product = products_by_id[product_id]
        if product.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock_quantity}."
                ),
            )

    total_amount = sum(
        (products_by_id[product_id].price * quantity
         for product_id, quantity in quantities.items()),
        start=Decimal("0.00"),
    )
    order = Order(total_amount=total_amount, currency=currencies.pop())
    for product_id, quantity in quantities.items():
        product = products_by_id[product_id]
        product.stock_quantity -= quantity
        order.items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=quantity,
            )
        )

    db.add(order)
    db.commit()
    return db.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order.id)
    )
