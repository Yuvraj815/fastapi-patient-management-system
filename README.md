# FastAPI Learning Notes

These are my notes from learning FastAPI and Pydantic while building the Patient Management System.

I have also written down some of the problems and confusions I faced while making this project and how I understood them.

---

# 1. What is FastAPI?

FastAPI is a Python framework used for building APIs.

A basic FastAPI application looks like:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello World"}
```

The `@app.get("/")` decorator tells FastAPI that this function handles GET requests for `/`.

---

# 2. Pydantic

Pydantic is used for data validation and parsing.

Example:

```python
from pydantic import BaseModel

class Patient(BaseModel):
    name: str
    age: int
```

When the API receives patient data, Pydantic checks whether the data follows the model.

---

# 3. Field

`Field()` can be used to add validation and additional information.

Example:

```python
age: Annotated[
    int,
    Field(gt=0, lt=100)
]
```

Here:

* `gt=0` means greater than 0
* `lt=100` means less than 100

---

# 4. Annotated

`Annotated` allows us to attach additional information or validation to a type.

Example:

```python
age: Annotated[int, Field(gt=0)]
```

The actual type is still `int`, but `Field` provides additional validation.

---

# 5. Literal

`Literal` restricts a value to specific choices.

Example:

```python
gender: Literal["male", "female"]
```

So values other than `male` or `female` will not be accepted.

---

# 6. Optional

`Optional` means that a value can also be `None`.

Example:

```python
name: Optional[str] = None
```

I used this concept in my `PatientUpdate` model because while updating a patient, the user may update only one or two fields.

---

# 7. computed_field

I used `computed_field` to calculate BMI automatically.

```python
@computed_field()
@property
def BMI(self) -> float:
    return round(self.weight / self.height ** 2, 2)
```

The user doesn't have to send the BMI. It is calculated from height and weight.

I also created a `verdict` computed field to determine whether the patient is Underweight, Normal, Overweight, or Obese.

---

# 8. model_dump()

One of the things I was initially confused about was `model_dump()`.

A Pydantic model is an object.

For example:

```python
patient
```

is a Pydantic object.

When I use:

```python
patient.model_dump()
```

it converts the Pydantic model into a Python dictionary.

So:

```text
Pydantic Model
      ↓
model_dump()
      ↓
Python Dictionary
```

This was useful when I wanted to save the patient data in JSON.

---

# 9. Why did I use `exclude=['id']`?

I used:

```python
patient.model_dump(exclude=['id'])
```

because I was already using the patient ID as the dictionary key.

For example:

```python
data[patient.id] = patient.model_dump(exclude=['id'])
```

The resulting structure looks like:

```json
{
    "P001": {
        "name": "Ananya",
        "city": "Guwahati",
        "age": 28
    }
}
```

There is no need to store `id` again inside the patient information because `P001` is already the key.

---

# 10. JSON File and Python Dictionary

I initially had some confusion about what happens when I load JSON data.

When I call:

```python
data = load_data()
```

the JSON file is read into memory.

The important thing I learned is:

```text
patient.json
     ↓
json.load()
     ↓
Python dictionary in memory
```

At this point, changing `data` does **not automatically change the JSON file**.

For example:

```python
data["P003"] = new_patient
```

only changes the dictionary in memory.

To actually save the change to the file, I need:

```python
save_data(data)
```

---

# 11. How `save_data()` Works

My `save_data()` function is:

```python
def save_data(data):
    with open("patient.json", "w") as f:
        json.dump(data, f)
```

I initially wondered whether this would append only the new patient to the JSON file.

What actually happens is:

```text
patient.json
      ↓
json.load()
      ↓
Complete data in memory
      ↓
Add/update/delete something
      ↓
save_data(data)
      ↓
JSON file is written again
```

So it does **not simply append patient P003** to the file.

Instead, the complete Python dictionary is written back to the JSON file.

The `"w"` mode means the file is opened for writing.

---

# 12. Adding a New Patient

For example, suppose the JSON contains:

{
    "P001": {
        "name": "Ananya"
    },
    "P002": {
        "name": "Rahul"
    }
}

If I add:

data["P003"] = {
    "name": "Aman"
}

the dictionary in memory becomes:

{
    "P001": {
        "name": "Ananya"
    },
    "P002": {
        "name": "Rahul"
    },
    "P003": {
        "name": "Aman"
    }
}

Then:

save_data(data)

writes this complete dictionary back to the file.

So P001 and P002 are not lost.

13. exclude_unset=True

This was another important concept I learned while making the update API.

Suppose the existing patient has:

{
    "name": "Ananya",
    "city": "Guwahati",
    "age": 28,
    "weight": 90
}

But I only want to change the weight:

{
    "weight": 75
}

Using:

patient.model_dump(exclude_unset=True)

gives:

{
    "weight": 75
}

This allows me to update only the fields that the user actually sent.

14. Patient vs PatientUpdate

I learned that these two models have different purposes.

Patient

Represents a complete patient:

class Patient(BaseModel):
    id: str
    name: str
    city: str
    age: int
    gender: Literal["male", "female"]
    height: float
    weight: float
PatientUpdate

Used when updating an existing patient:

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Literal["male", "female"]] = None
    height: Optional[float] = None
    weight: Optional[float] = None

The reason for having a separate update model is that I don't want to force the user to send every field when they only want to change one field.

15. The Update Bug I Faced

This was one of the bugs I faced while making the project.

I created the complete updated Pydantic object:

patient_pydantic_obj = Patient(**existing_patient_info)

But after that, I accidentally wrote:

existing_patient_info = patient.model_dump(exclude=['id'])

Here, patient was the PatientUpdate object, not the complete Patient object.

So I was dumping the wrong object.

The correct code is:

existing_patient_info = patient_pydantic_obj.model_dump(
    exclude=['id']
)

The important thing I learned was:

PatientUpdate
     ↓
contains only fields sent for update

Patient
     ↓
contains the complete patient
     ↓
BMI + verdict are calculated

So after creating the complete Patient object, I need to dump that object.

16. Update Flow

The complete update flow became much clearer to me after debugging it:

Update request
      ↓
PatientUpdate
      ↓
Load existing patient
      ↓
Get only fields provided by user
      ↓
Update existing data
      ↓
Create complete Patient object
      ↓
Pydantic validation
      ↓
BMI + verdict calculated
      ↓
model_dump()
      ↓
save_data()
      ↓
JSON file updated
17. Path Parameters

A path parameter is a value inside the URL.

Example:

@app.get("/patient/{patient_id}")
def patient(patient_id: str):
    ...

If I request:

/patient/P001

then:

patient_id = "P001"
18. Query Parameters

Query parameters are values passed after ?.

For example:

/sort?sort_by=weight&order=desc

The function receives:

sort_by = "weight"
order = "desc"

I used query parameters for sorting patients.

19. Sorting Confusion

I initially used:

valid_fields = ['height', 'weight', 'bmi']

But my computed field was named:

BMI

with capital letters.

This taught me that field names need to match when accessing dictionary data.

For example:

x.get("bmi")

and:

x.get("BMI")

are different keys.

20. HTTPException

I learned that HTTPException can be used when something goes wrong.

For example:

raise HTTPException(
    status_code=404,
    detail="Patient not found"
)

This returns an appropriate HTTP error response instead of simply returning a normal Python error.

21. JSON Error / Trailing Comma

I also faced a JSON error when I wrote:

{
    "id": "P001",
    "name": "Ananya Verma",
    "city": "Guwahati",
    "age": 28,
    "gender": "female",
    "height": 1.65,
    "weight": 90,
}

The problem was the comma after the last value:

"weight": 90,

JSON does not allow a trailing comma before }.

Correct:

"weight": 90

This helped me understand that JSON syntax is stricter than Python dictionaries.

22. Uvicorn

Uvicorn is the server used to run the FastAPI application.

I used:

uvicorn main:app --reload

Here:

main → main.py
app → FastAPI object
--reload → automatically reloads when the code changes

I initially made a small spelling mistake:

uvicorn main: app --relode

The correct command is:

uvicorn main:app --reload
23. Swagger

FastAPI automatically provides interactive API documentation.

I can open:

http://127.0.0.1:8000/docs

and test my API directly from the browser.

This was useful because I didn't have to use Postman for every test.

24. Git and GitHub

While finishing the project, I also learned how to upload a FastAPI project to GitHub.

Some commands I learned:

git init
git status
git add .
git commit -m "Initial project"
git branch -M main
git remote add origin <repository-url>
git push -u origin main

I also learned why .gitignore is important.

For example, I don't want to upload:

.venv/
myenv/
.idea/
__pycache__/
patient.json

to GitHub.

25. Git Repository Mistake I Faced

I accidentally initialized Git in:

C:\Users\yuvra

instead of:

C:\Users\yuvra\Desktop\fast_api

Because of this, git status started showing things like:

Documents/
Downloads/
AppData/
anaconda3/
PycharmProjects/

I understood that Git was treating my entire user directory as the repository.

I removed the incorrect .git repository and initialized Git inside the actual project folder.

After fixing it:

C:\Users\yuvra\Desktop\fast_api

became the Git repository.

This was a useful lesson about understanding where git init is executed.

26. My Overall Learning

The biggest thing I learned from this project is that I should not just copy code.

When something breaks, understanding why it broke is more useful.

Some of the main concepts that confused me initially were:

How Pydantic models work
Difference between a Pydantic object and a dictionary
What model_dump() does
What exclude_unset=True does
How JSON data is loaded into memory
How changes are written back to the JSON file
Difference between Patient and PatientUpdate
How computed fields work
How FastAPI path and query parameters work
Why JSON doesn't allow trailing commas
How Uvicorn runs a FastAPI application
How Git tracks files
Why .gitignore is needed
Why Git must be initialized in the correct project directory

This project is still a learning project, and I plan to improve it as I learn more about FastAPI, databases, authentication, testing, and deployment.
