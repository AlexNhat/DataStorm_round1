import asyncio, json
from app.routers.cognitive_api import generate_strategies, StrategyRequest

async def main():
    resp = await generate_strategies(StrategyRequest())
    print('strategies', len(resp['strategies']))
    json.dumps(resp)
    print('json ok')

asyncio.run(main())
