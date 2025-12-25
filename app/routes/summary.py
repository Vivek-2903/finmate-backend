from fastapi import APIRouter, HTTPException
from typing import List, Dict
from datetime import datetime
from collections import defaultdict

router = APIRouter()

@router.post("/financial-summary")
async def financial_summary(transactions: List[Dict]):
    """
    Summarize financial data monthly from the given transactions.
    Input: List of transactions with at least 'date' and 'amount'
    """

    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions provided.")

    monthly_data = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "savings": 0.0})
    overall_income = 0.0
    overall_expense = 0.0
    categories = defaultdict(float)

    for txn in transactions:
        try:
            date_str = txn.get("date")
            amount = float(txn.get("amount", 0))
            desc = txn.get("description", "").lower()

            if not date_str:
                continue

            # Normalize to YYYY-MM for grouping
            try:
                month = datetime.fromisoformat(date_str).strftime("%Y-%m")
            except Exception:
                continue

            # Income or expense classification
            if amount > 0:
                monthly_data[month]["income"] += amount
                overall_income += amount
            else:
                monthly_data[month]["expense"] += abs(amount)
                overall_expense += abs(amount)

            # Categorize spending
            if any(k in desc for k in ["salary", "credit", "deposit", "payroll"]):
                categories["Salary"] += abs(amount)
            elif any(k in desc for k in ["swiggy", "zomato", "food", "restaurant"]):
                categories["Food & Dining"] += abs(amount)
            elif any(k in desc for k in ["petrol", "fuel", "uber", "ola", "transport"]):
                categories["Transport"] += abs(amount)
            elif any(k in desc for k in ["bill", "recharge", "netflix", "subscription", "electricity"]):
                categories["Bills & Utilities"] += abs(amount)
            elif any(k in desc for k in ["mutual", "sip", "investment", "stock"]):
                categories["Investments"] += abs(amount)
            elif any(k in desc for k in ["rent", "maintenance", "society"]):
                categories["Housing"] += abs(amount)
            else:
                categories["Other"] += abs(amount)

        except Exception as e:
            print(f"⚠️ Skipping transaction due to error: {e}")

    # Compute monthly savings
    for month, data in monthly_data.items():
        data["savings"] = data["income"] - data["expense"]

    # Compute overall summary
    net_savings = overall_income - overall_expense
    saving_ratio = (net_savings / overall_income * 100) if overall_income else 0

    # Sort months chronologically
    monthly_summary = [
        {"month": m, **vals} for m, vals in sorted(monthly_data.items())
    ]

    # Top 3 expense categories
    top_expenses = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]

    insights = {
        "overall_income": round(overall_income, 2),
        "overall_expense": round(overall_expense, 2),
        "net_savings": round(net_savings, 2),
        "saving_ratio": round(saving_ratio, 2),
        "top_expense_categories": [
            {"category": c, "amount": round(a, 2)} for c, a in top_expenses
        ],
        "monthly_summary": monthly_summary,
        "categories_breakdown": categories,
        "generated_at": datetime.now().isoformat(),
    }

    return {"message": "Summary generated successfully", "summary": insights}
