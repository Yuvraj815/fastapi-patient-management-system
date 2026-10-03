from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import JSONResponse
from fastapi import Path
from pydantic import BaseModel,Field,computed_field
from typing import Annotated,Literal,Optional

class Patient(BaseModel):
    id : Annotated[str,Field(...,description="Id of patient ",examples=['P001'])]
    name: Annotated[str,Field(...,description='Name of the patient')]
    city: Annotated[str,Field(...,description="City of the patient")]
    age: Annotated[int,Field(...,gt=0,lt=100,description="Age of the patient")]
    gender: Annotated[Literal['male','female'],Field(...,description="Gender of the patient")]
    height: Annotated[float,Field(...,gt=0,description="Height of the patient")]
    weight: Annotated[float,Field(...,gt=0,description="Weight of the patient")]



    @computed_field()
    @property
    def BMI(self)->float:
        bmi = round((self.weight/self.height**2),2)
        return bmi


    @computed_field()
    @property
    def verdict(self)->str:

        if self.BMI < 18.5:
            return 'Underweight'
        elif self.BMI < 25:
            return 'Normal'
        elif self.BMI < 30:
            return 'Overweight'
        else:
            return 'Obes'





class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None)]
    weight: Annotated[Optional[float], Field(default=None)]

app = FastAPI()
import json
def load_data():
    with open("patient.json", "r") as f:
        data = json.load(f)
        return data
def save_data(data):
    with open("patient.json", "w") as f:
        json.dump(data, f)
@app.get("/")
def hello_world():
    return {"message": "Patient Management System API "}
@app.get('/about')
def about():
    return {'message': "A fully function API to manage patient details"}
@app.get("/view")
def view():
    data = load_data()
    return data
@app.get('/patient/{patient_id}')
def patient(patient_id:str = Path(...,description="The id of patient in the db",example='P001')):
    data = load_data()
    if  patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")
@app.get('/sort')
def sort_patient(sort_by:str=Query(...,description="Sort on the basis of height,weight,or bmi"), order: str=Query('asc',description='sort in asc or desc order')):
    valid_fields = ['height','weight','bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,detail="Sort by must be one of {}".format(valid_fields))
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400,detail="Invalid order select between asc and desc" )
    sort_order = True if order == 'desc' else False
    data = load_data()
    sorted_data = sorted(data.values(), key= lambda x:x.get(sort_by,0), reverse= sort_order)
    return sorted_data
@app.post('/create')
def create_patient(patient:Patient):
     # Lode the data
    data = load_data()
     # Check the patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400,detail="Patient already exists")
    # New patient add to the database
    data[patient.id]=patient.model_dump(exclude=['id'])
    save_data(data)


    return JSONResponse(status_code=201,content="The patient  detail add successfully ")
@app.put("/edit/{patient_id}")
def update_patient(patient_id:str,patient:PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=400,detail="Patient not found")
    existing_patient_info = data[patient_id] # it gives the value of the patient all details

    updated_patient_info = patient.model_dump(exclude_unset=True) # model_dump -> it convert the patient obj to the dictainory
    for key ,value in updated_patient_info.items():
        existing_patient_info[key] = value

    #existing_patient_info -> pydentic obj -> updated BMI + verdict
    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)
    #pydantic obj -> dict
    existing_patient_info = patient.model_dump(exclude  ='id')
   # add dict to data
    data[patient_id] = existing_patient_info
    #save data
    save_data(data)
    return JSONResponse(status_code=200,content="The patient detail update successfully ")
@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=400,detail="Patient not found")
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200,content="The patient detail delete successfully ")