"""Labor auto-generated untuk melengkapi relasi."""
def load_labor_auto_generated(kg):
    from fastra_core.knowledge.nodes import LaborNode
    from fastra_core.primitives.currency import Currency
    items = [
    ]
    for args in items:
        kg.add_labor(LaborNode(*args))
    print(f"  ✅ Labor Auto-Generated: {len(items)} labor dimuat")
