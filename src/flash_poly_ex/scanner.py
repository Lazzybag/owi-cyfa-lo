import os, json, time
from tqdm import tqdm
import pandas as pd
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("POLYGON_RPC")))
assert w3.is_connected(), "RPC dead"

PAIR_ABI   = json.loads("""[{"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]""")
FACTORY_ABI= json.loads('[{"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')
ERC20_ABI  = json.loads('[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]')

UNI_V2_FACTORY = "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"
USDC           = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

factory = w3.eth.contract(address=Web3.to_checksum_address(UNI_V2_FACTORY), abi=FACTORY_ABI)
n_pairs = min(factory.functions.allPairsLength().call(), 50)

def get_price_usd(res0, res1, dec0, dec1, usd_index=0):
    if usd_index == 0: return res0 / (res1 * 10**(dec0 - dec1))
    return res1 / (res0 * 10**(dec1 - dec0))

results = []
for i in tqdm(range(n_pairs), desc="scan"):
    pair_addr = factory.functions.allPairs(i).call()
    pair = w3.eth.contract(address=pair_addr, abi=PAIR_ABI)
    try:
        tok0, tok1 = pair.functions.token0().call(), pair.functions.token1().call()
        res0, res1, _ = pair.functions.getReserves().call()
        t0 = w3.eth.contract(address=tok0, abi=ERC20_ABI)
        t1 = w3.eth.contract(address=tok1, abi=ERC20_ABI)
        dec0, dec1 = t0.functions.decimals().call(), t1.functions.decimals().call()
        sym0, sym1 = t0.functions.symbol().call(), t1.functions.symbol().call()
    except: continue

    tvl_usd = 2 * (res0/10**dec0) * get_price_usd(res0, res1, dec0, dec1, 0 if tok0==USDC else 1)
    if tvl_usd >= 50_000: continue

    results.append({
        "pair": pair_addr,
        "symbol": f"{sym0}-{sym1}",
        "tvl_usd": round(tvl_usd, 2),
        "collateral_factor": 75,
        "uses_twap": False,
        "shared_feed": True
    })
    time.sleep(0.2)

df = pd.DataFrame(results)
df.to_csv("data/targets.csv", index=False)
print("✅ targets.csv ready – ", len(df), "pools")
