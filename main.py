from fastapi import FastAPI,Path,HTTPException,Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel ,Field,computed_field
from typing import Annotated,Literal,Optional
import json

app = FastAPI()


class patient(BaseModel):
    id: Annotated[str,Field(..., description='Id of the patient',examples=['P001'])] 
    name: Annotated[str,Field(..., description='name of the patient')]
    age:Annotated[int,Field(...,gt=0,lt=120,description='Age of the patient')] 
    city:Annotated[str,Field(...,description='city where the patient is living')]
    gender: Annotated[Literal['male','female','others'],Field(...,description='gender of the patient')]
    height: Annotated[float,Field(..., gt=0,description='height of the patient in mtrs')]
    weight:Annotated[float,Field(...,gt=0,description='weight of the patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
        
    @computed_field
    @property
    def verdict(self) -> str:

        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Normal'
        else:
            return 'Obese'

class PatientUpdate(BaseModel):  #this pydantic model is for put http method/ for updating data
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]
     
                                                                         


def load_data():  #for recive the data
    with open("patient.json","r") as f:
        data=json.load(f)
    return data

def save_data(data):   #for post the data
    with open('patient.json', 'w') as f:
        json.dump(data, f)

@app.get("/")
def hello():
    return {"message": "Patient Management System API"}


@app.get("/about")
def about():
    return {"message":"A fully Functional API to manage your patient records"}

@app.get("/view")
def view():
    data= load_data()
    return data

@app.get('/patient/{patient_id}')
def view_patient(patient_id:str = Path(...,description='ID of the patient in DB',example='P001')): #(path parameter) here we can see after str type we can give a path, its increses readibility for user to use our software, ... means its required.
    #load all the patient  
    data=load_data()

    if  patient_id in data:
        return data[patient_id]  # now we can access a particular data in dictionary in python.
    # return {'error':'patient not found'}
    raise HTTPException(status_code=404,detail='patient not found')


@app.get('/sort') #starts query() parameter
def sort_patients(sort_by: str = Query(..., description='Sort on the basis of height, weight or bmi'),  order: str = Query( 'asc', description='sort in asc or desc order')): # asc is default parameter of {order} key  and  ... is required to fill for {sort_by} key
    valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f'Invalid field select from {valid_fields}')
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail='Invalid order select between asc and desc')
    
    data = load_data()

    sort_order = True if order=='desc' else False

    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order)

    return sorted_data 

@app.post('/create')  # This API endpoint will run when a POST request is sent to "/create"
def create_patient(p: patient):  # Function that takes patient data from request body
    
    # load existing data
    data = load_data()  # Load already saved patient data from the JSON file
    
    # check if the patient already exists
    if p.id in data:  # Check if the patient ID already exists in the database
        raise HTTPException(status_code=400, detail='patient already exists')  
        # If ID exists, raise an error with status 400 (Bad Request)
    
    # new patient add to the database
    data[p.id] = p.model_dump(exclude=['id'])  
    # Add new patient data into dictionary
    # model_dump() converts Pydantic model into dictionary
    # exclude=['id'] means we are not saving id inside the patient details again
    
    # save into the json file
    save_data(data)  # Save updated data back into the JSON file
    
    return JSONResponse(status_code=201, content={'message':'patient created successfully'})  
    # Return success response with status 201 (Created) 

@app.put('/edit/{patient_id}')  # strating put endpoint for update
def update_patient(patient_id: str, patient_update: PatientUpdate):

    data = load_data()

    if patient_id not in data:   #check patient id in data or not
        raise HTTPException(status_code=404, detail='Patient not found')
    
    existing_patient_info = data[patient_id] #existing particular data from particular patient id

    updated_patient_info = patient_update.model_dump(exclude_unset=True)  #converting pydantic model to dictionary.

    for key, value in updated_patient_info.items(): # creating a loop for extract key and value
        existing_patient_info[key] = value

   
    existing_patient_info['id'] = patient_id
    patient_pydandic_obj = patient(**existing_patient_info)
 
    existing_patient_info = patient_pydandic_obj.model_dump(exclude='id')

    
    data[patient_id] = existing_patient_info

    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient updated'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):

    # load data
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient deleted'})