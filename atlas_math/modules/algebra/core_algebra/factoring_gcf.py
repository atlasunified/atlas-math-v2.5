from __future__ import annotations

import itertools
import math
import random
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = ["{instruction}: {problem}", "Solve and report the result: {problem}", "Work the problem and give the final answer: {problem}", "Compute the requested result: {problem}"]
MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try: value = int(str(difficulty).rsplit('_', 1)[-1])
    except Exception: value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str: return '|'.join(str(p) for p in parts)

def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)): break
        yield item

MODULE_INFO = {"module_id": "algebra.factoring_gcf", "name": "Factoring GCF", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 850, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"numeric_gcf": 700}, "level_2": {"monomial_gcf": 850}, "level_3": {"binomial_gcf": 1000}, "level_4": {"trinomial_gcf": 1200}, "level_5": {"signed_gcf": 1400}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}


def _spec(family, values, problem, answer):
    canonical=':'.join([family]+[str(v) for v in values])
    return {"family":family,"values":values,"problem":problem,"answer":answer,"canonical_key":canonical,"case_id":canonical,"family_id":family}


def _sample_from_spec(spec,difficulty,instruction_idx=0):
    answer=spec['answer']
    metadata={"family":spec['family'],"level_number":_level_num(difficulty),"structured":True,"canonical_key":spec['canonical_key'],"case_id":spec['case_id'],"family_id":spec['family_id'],"template_id":spec['family'],"final_answer":answer,"values":list(spec.get('values',[]))}
    instruction=INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Factor out the greatest common factor", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emitted=0
    for g in range(2,13):
        for a in range(2,13):
            for b in range(2,13):
                n1,n2=g*a,g*b
                yield _spec('numeric_gcf',(g,a,b),f"Factor the GCF from {n1} + {n2}.",f"{g}({a} + {b})")
                emitted+=1
                if emitted>=FAMILY_CAPS['level_1']['numeric_gcf']: return

def iter_level2_specs():
    emitted=0
    for g in range(2,13):
        for p in range(1,6):
            for q in range(1,6):
                for a in range(2,8):
                    for b in range(2,8):
                        t1=g*a; t2=g*b
                        ans=f"{g}x^{min(p,q)}({a}x^{p-min(p,q)} + {b}x^{q-min(p,q)})"
                        yield _spec('monomial_gcf',(g,p,q,a,b),f"Factor the GCF from {t1}x^{p} + {t2}x^{q}.",ans)
                        emitted+=1
                        if emitted>=FAMILY_CAPS['level_2']['monomial_gcf']: return

def iter_level3_specs():
    emitted=0
    for g in range(2,13):
        for a in range(1,8):
            for b in range(1,8):
                for c in range(1,8):
                    ans=f"{g}({a}x + {b})"
                    yield _spec('binomial_gcf',(g,a,b),f"Factor the GCF from {g*a}x + {g*b}.",ans)
                    emitted+=1
                    if emitted>=FAMILY_CAPS['level_3']['binomial_gcf']: return

def iter_level4_specs():
    emitted=0
    for g in range(2,13):
        for a in range(1,7):
            for b in range(1,7):
                for c in range(1,7):
                    ans=f"{g}({a}x^2 + {b}x + {c})"
                    yield _spec('trinomial_gcf',(g,a,b,c),f"Factor the GCF from {g*a}x^2 + {g*b}x + {g*c}.",ans)
                    emitted+=1
                    if emitted>=FAMILY_CAPS['level_4']['trinomial_gcf']: return

def iter_level5_specs():
    emitted=0
    for g in range(2,13):
        for a in range(1,7):
            for b in range(1,7):
                ans=f"-{g}({a}x - {b})"
                yield _spec('signed_gcf',(g,a,b),f"Factor out -{g} from -{g*a}x + {g*b}.",ans)
                emitted+=1
                if emitted>=FAMILY_CAPS['level_5']['signed_gcf']: return


def _iter_specs(difficulty='level_1'):
    level=_level_num(difficulty)
    if level==1:return _take(iter_level1_specs(),LEVEL_SPEC_CAPS['level_1'])
    if level==2:return _take(iter_level2_specs(),LEVEL_SPEC_CAPS['level_2'])
    if level==3:return _take(iter_level3_specs(),LEVEL_SPEC_CAPS['level_3'])
    if level==4:return _take(iter_level4_specs(),LEVEL_SPEC_CAPS['level_4'])
    return _take(iter_level5_specs(),LEVEL_SPEC_CAPS['level_5'])


def curriculum(): return {'level_1':['factor numeric common factors'],'level_2':['factor monomial common factors'],'level_3':['factor common factors from binomials'],'level_4':['factor common factors from trinomials'],'level_5':['manage sign choices while factoring the GCF']}

def estimate_capacity(difficulty='level_1'): return dict(CAPACITY_HINTS.get(difficulty, {'value': None, 'quality': 'unknown'}))

def generate(count=10,difficulty='level_1',seed=None):
    count=max(0,int(count)); prefix=min(max(count*MAX_GENERATE_MULTIPLIER,256),MAX_SPEC_PREFIX); pool=list(itertools.islice(_iter_specs(difficulty),0,prefix));
    if not pool or count==0:return []
    rng=random.Random(_stable_seed(MODULE_INFO['module_id'],difficulty,seed,'generate')); rng.shuffle(pool); return [_sample_from_spec(spec,difficulty,i) for i,spec in enumerate(pool[:count])]

def generate_unique(count=10,difficulty='level_1',offset=0,stride=1,seed=None):
    count=max(0,int(count)); offset=max(0,int(offset)); stride=max(1,int(stride)); pool=list(itertools.islice(_iter_specs(difficulty),0,MAX_SPEC_PREFIX)); rng=random.Random(_stable_seed(MODULE_INFO['module_id'],difficulty,seed,offset,stride,'unique')); rng.shuffle(pool); seen=set(); ordered=[]
    for spec in pool:
        if spec['canonical_key'] in seen: continue
        seen.add(spec['canonical_key']); ordered.append(spec)
    return [_sample_from_spec(spec,difficulty,i) for i,spec in enumerate(ordered[offset::stride][:count])]

def iter_samples(difficulty='level_1',seed=None):
    max_items=min(LEVEL_SPEC_CAPS.get(difficulty,1000),MAX_ITER_SAMPLES); pool=list(itertools.islice(_iter_specs(difficulty),0,max_items)); rng=random.Random(_stable_seed(MODULE_INFO['module_id'],difficulty,seed,'iter')); rng.shuffle(pool); seen=set()
    for idx,spec in enumerate(pool):
        if spec['canonical_key'] in seen: continue
        seen.add(spec['canonical_key']); yield _sample_from_spec(spec,difficulty,idx)


