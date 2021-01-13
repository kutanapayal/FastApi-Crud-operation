from fastapi import FastAPI
from fastapi.params import Depends
from pydantic import BaseModel,Field
from datetime import datetime
import databases
from typing import List
import sqlalchemy
from setuptools.command.register import register

DATABASE_URL="sqlite:///./store.db"

metadata= sqlalchemy.MetaData()

database = databases.Database(DATABASE_URL)

register=sqlalchemy.Table(
    "reigister",
    metadata,
    sqlalchemy.Column("id",sqlalchemy.Integer,primary_key=True),
    sqlalchemy.Column("name",sqlalchemy.String(500)),
    sqlalchemy.Column("date_created",sqlalchemy.DateTime())
)

engine=sqlalchemy.create_engine(
    DATABASE_URL,connect_args={"check_same_thread":False}
)

metadata.create_all(engine)

app=FastAPI()

@app.on_event("startup")
async def connect():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

class RegisterIn(BaseModel):
    name:str=Field(...)

class Register(BaseModel):
    id:int
    name:str
    date_created:datetime

@app.post('/register/',response_model=Register)
async def create(r: RegisterIn = Depends()):
    query = register.insert().values(
        name=r.name,
        date_created=datetime.utcnow()
    )
    record_id=await database.execute(query)
    query=register.select().where(register.c.id == record_id)
    row=await database.fetch_one(query)
    return {**row}

@app.get('/register/{id}',response_model=Register)
async def get_one(id: int):
    query = register.select().where(register.c.id==id)
    user=await database.fetch_one(query)
    return {**user}


@app.get('/register/',response_model=List[Register])
async def get_all():
    query = register.select()
    data=await database.fetch_all(query)
    return data

@app.put('/register/{id}',response_model=Register)
async def update(id:int,r:RegisterIn=Depends()):

    query=register.update().where(register.c.id==id).values(
        name=r.name,
        date_created=datetime.utcnow()
    )
    row_id=await database.execute(query)
    user=register.select().where(register.c.id==row_id)
    row=await database.fetch_one(user)
    return {**row}

@app.delete('/register/{id}')
async def delete(id: int):
    query = register.delete().where(register.c.id==id)
    try:
        return await database.execute(query)
    except Exception as e:
        return {"Not Found id :":id}
