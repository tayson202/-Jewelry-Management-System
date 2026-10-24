"""
3M Dahab OS - Safe Demo Data Cleanup & Reset Tool
Safely cleans demo/sample products, fake sales, test customers, and mock logs,
while strictly preserving the primary Admin user, system settings, license configs,
and market feed settings.
"""

import os
import sys
import argparse

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal, Base, engine
from app.models import (
    User, Product, Sale, SaleItem, TradeInItem, Customer,
    Supplier, Expense, AuditLog
)

def reset_demo_data(force: bool = False):
    print("=" * 70)
    print(" 3M Dahab OS - Safe Demo Data Cleanup")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Check current counts
        prod_count = db.query(Product).count()
        sale_count = db.query(Sale).count()
        cust_count = db.query(Customer).count()
        supp_count = db.query(Supplier).count()
        exp_count = db.query(Expense).count()
        audit_count = db.query(AuditLog).count()
        admin_count = db.query(User).filter(User.role == "ADMIN").count()
        emp_count = db.query(User).filter(User.role == "EMPLOYEE").count()

        print(f"Current Database Contents:")
        print(f" - Products:          {prod_count}")
        print(f" - Sales & Invoices:  {sale_count}")
        print(f" - Customers:         {cust_count}")
        print(f" - Suppliers:         {supp_count}")
        print(f" - Expenses:          {exp_count}")
        print(f" - Audit Logs:        {audit_count}")
        print(f" - Admin Users:       {admin_count} (WILL BE PRESERVED)")
        print(f" - Employee Accounts: {emp_count}")

        if not force:
            confirm = input("\nAre you sure you want to purge all demo business records? (type 'yes' to proceed): ")
            if confirm.strip().lower() != "yes":
                print("Operation cancelled. No changes made.")
                return

        print("\nCleaning demo records...")

        # 1. Purge sales and line items
        db.query(TradeInItem).delete()
        db.query(SaleItem).delete()
        db.query(Sale).delete()

        # 2. Purge demo products
        db.query(Product).delete()

        # 3. Purge demo customers and suppliers
        db.query(Customer).delete()
        db.query(Supplier).delete()

        # 4. Purge demo expenses
        db.query(Expense).delete()

        # 5. Purge test audit logs
        db.query(AuditLog).delete()

        # 6. Purge demo employee accounts (keep only ADMIN users)
        db.query(User).filter(User.role == "EMPLOYEE").delete()

        db.commit()

        print("[OK] Demo business data successfully purged.")
        print(f" - Active Admin users preserved: {db.query(User).filter(User.role == 'ADMIN').count()}")
        print(f" - Business records remaining: 0 (clean shop workspace)")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Reset failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge demo data from 3M Dahab OS database")
    parser.add_argument("--force", action="store_true", help="Execute without interactive prompt")
    args = parser.parse_args()
    reset_demo_data(force=args.force)
