import json
data = json.load(open('proofs/runs/20261002_094726/proof_ladder_report.json'))
print(f'Total: {data["total_steps"]}, PASS: {data["passed"]}, FAIL: {data["failed"]}')
print()
for r in data['results']:
    print(f'{r["step"]}: {r["status"]} ({r["elapsed_seconds"]:.2f}s)')
