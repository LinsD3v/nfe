from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic.types import Decimal

app = FastAPI(name='Potato commander', version='0.0.1', description='A simple api to command AHK scripts to NFE emission.')


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
    client: client_model
    items: list[item_model] = Field(min_length=1)


@app.get('/life')
def life():
    return {'message': 'Life is good!'}

@app.post('/nfe')
def nfe(data: nfe_data_model):
    # Here you can add the logic to handle the NFE data, such as calling an AHK script or processing the data.
    return {'message': 'NFE data received successfully!', 'data': data.dict()}