from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic.types import Decimal

app = FastAPI(name='Potato commander', version='0.0.1', description='A simple api to command AHK scripts to NFE emission.')

class adress_model(BaseModel):
    street_name: str
    number: str
    street_type: str
    cep: str
    

class client_model(BaseModel):
    name: str
    cpf: str
    adress: adress_model


class item_model(BaseModel):
    name: str
    sku: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)


class nfe_data_model(BaseModel):
    client: client_model
    items: list[item_model] = Field(min_length=1)


@app.get('/life')
def life():
    return {'message': 'Life is good!'}

