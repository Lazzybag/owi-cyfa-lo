#!/usr/bin/env python3
import os, csv, json
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://polygon-bor-rpc.publicnode.com"))
assert w3.is_connected(), "RPC dead"

UNITROLLER = Web3.to_checksum_address('0x8849f1a0cb6b5dbfec34f3ef5515f071bf2c6c99')
abi = [{'inputs':[{'name':'','type':'address'}],'name':'markets','outputs':[{'name':'collateralFactorMantissa','type':'uint256'}],'stateMutability':'view','type':'function'}]
comptroller = w3.eth.contract(address=UNITROLLER, abi=abi)

with open('data/targets.csv') as f:
    for _ in range(2): next(f, None)  # skip header + blank
    for line in f:
        row = [x.strip().strip('"') for x in line.strip().split(',')]
        if len(row) < 3: continue
        pair, symbol, tvl_str = row[0], row[1], row[2]
        if not tvl_str.replace('.','').isdigit(): continue
        tvl = float(tvl_str)
        if tvl * 0.02 > 10: continue      # $10 max move-cost
        try:
            raw = comptroller.functions.markets(Web3.to_checksum_address(pair)).call()
            cf = raw[0] / 1e18 * 100
        except: continue                   # not listed → skip
        if cf >= 30:                       # ANY listed pool
            print(f"VICTIM FOUND: {pair}  {symbol}  TVL=${tvl:.2f}  CF={cf:.1f}%")
            with open('victim.txt','w') as out:
                out.write(f"{pair},{symbol},{tvl},{cf}\n")
            exit(0)
print("Still no eligible pool (CF ≥ 30 %) in mUnitroller.")
