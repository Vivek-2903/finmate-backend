from fastapi import APIRouter, HTTPException
from typing import List, Dict
from datetime import datetime
import statistics

router = APIRouter()

@router.post("/analyze-transactions")
async def analyze_transactions(transactions: List[Dict]):
    """
    Analyze uploaded bank transactions and return categorized insights.
    Input: list of dicts (each with date, amount, description, etc.)
    """

    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions provided.")

    # Basic preprocessing
    total_income = 0.0
    total_expense = 0.0
    categories = {}

    for t in transactions:
        amount = float(t.get("amount", 0))
        desc = t.get("description", "").lower()

        # Determine type
        if amount > 0:
            txn_type = "credit"
            total_income += amount
        else:
            txn_type = "debit"
            total_expense += abs(amount)

        # Categorize based on description keywords
        category = "Other"
        if any(k in desc for k in ["salary", "credit", "deposit", "payroll"]):
            category = "Salary"
        elif any(k in desc for k in ["upi", "amazon", "swiggy", "zomato", "food", "restaurant"]):
            category = "Food & Dining"
        elif any(k in desc for k in ["petrol", "fuel", "transport", "uber", "ola"]):
            category = "Transport"
        elif any(k in desc for k in ["electricity", "bill", "gas", "internet", "netflix", "subscription"]):
            category = "Bills & Utilities"
        elif any(k in desc for k in ["mutual", "sip", "investment", "demat", "stock"]):
            category = "Investments"
        elif any(k in desc for k in ["rent", "maintenance", "society"]):
            category = "Housing"

        # Store category totals
        categories[category] = categories.get(category, 0) + abs(amount)

    net_savings = total_income - total_expense
    saving_ratio = (net_savings / total_income * 100) if total_income else 0

    # Top 3 spending categories
    top_expenses = sorted(
        ((k, v) for k, v in categories.items() if v > 0),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    insights = {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(net_savings, 2),
        "saving_ratio": round(saving_ratio, 2),
        "top_expense_categories": [
            {"category": c, "amount": round(a, 2)} for c, a in top_expenses
        ],
        "categories_breakdown": categories,
        "generated_at": datetime.now().isoformat(),
    }

    return {"message": "Analysis successful", "summary": insights}
