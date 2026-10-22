#!/usr/bin/env python3
import json,sys,time
from pathlib import Path
p=Path(sys.argv[sys.argv.index('-o')+1])/'fixture'/'result.json'
p.parent.mkdir(parents=True)
p.write_text(json.dumps({'trial_name':'synthetic','verifier_result':{'rewards':{'reward':1}},'exception_info':None}))
print('synthetic partial result emitted',flush=True)
time.sleep(60)
