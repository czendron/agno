# -------------------------------------------------------
# BANK ACCOUNT - FastAPI
# to manage customers' withdraws and deposits
# -------------------------------------------------------

# IMPORTS ------------------------
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel, Field

# Add customers
db_customers = {
    "John": 19170.98,
    "Alice": 2304.18,
    "Bob": 85832.65,
}

# Create a class for the transactions. (use pydantic to avoid mistakes)
class Transaction(BaseModel):
    customer: str = Field(..., description="Customer name")
    value: float = Field(..., gt=0, description="Transaction value")

# Create an enpoint HOME (root)
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to the Bank Account API"}

    
# Create an endpoint to check balance
@app.post("/balance")
def balance(customer: str):
    return {"message": f"Balance - {customer}: {db_customers[customer]}"}

# Create an enpoint to make withdraws
@app.post("/withdraw")
def withdraw(transaction: Transaction):
    customer = transaction.customer
    value = transaction.value
    if customer not in db_customers:
        return {"error": f"Customer '{customer}' does not exist."}
    if db_customers[customer] < value:
        return {"error": "Insufficient funds."}
    db_customers[customer] -= value
    return {"message": {"Customer": customer}, "Withdrawn": -value, "New balance": db_customers[customer]}


# Create an enpoint to make deposits
@app.post("/deposit")
def deposit(transaction: Transaction):
    customer = transaction.customer
    value = transaction.value
    if customer not in db_customers:
        return {"error": f"Customer '{customer}' does not exist."}
    db_customers[customer] += value
    return {"message": {"Customer": customer, "Deposit": +value, "New balance": db_customers[customer]}}

# Create a

# RUN ===============================================
if __name__ == "__main__":
    uvicorn.run("example_2:app", host="0.0.0.0", port=8000, reload=True)

