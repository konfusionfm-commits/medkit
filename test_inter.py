import httpx

from medkit.interactions import InteractionEngine
from medkit.providers.openfda import OpenFDAProvider

client = httpx.Client()
provider = OpenFDAProvider(client)
engine = InteractionEngine()

drugs = ["aspirin", "warfarin"]
print(f"Testing {drugs}...")
warnings = engine.check_sync(drugs, provider)
for w in warnings:
    print(w)

drugs2 = ["metformin", "glipizide"]
print(f"Testing {drugs2}...")
warnings2 = engine.check_sync(drugs2, provider)
for w in warnings2:
    print(w)

print("Done")
