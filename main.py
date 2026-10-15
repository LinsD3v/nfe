from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic.types import Decimal
from repositories.orders import (
    registrar_pedido,
    buscar_pedido,
    receber_pedido,
)

app = FastAPI(title='Potato commander', version='0.0.1', description='A simple api to command AHK scripts to NFE emission.')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://dmgnimpjekpjgfhbepngccjdffoaibge"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

class client_model(BaseModel):
    name: str
    cpf: str
    address: str


class item_model(BaseModel):
    name: str
    sku: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)


class nfe_data_model(BaseModel):
    order_id: str
    client: client_model
    items: list[item_model] = Field(min_length=1)


@app.get('/life')
def life():
    return {'message': 'Life is good!'}

@app.post('/nfe')
def nfe(data: nfe_data_model):
    return receber_pedido(
        data.order_id, 
        data.model_dump(mode='json')
        )