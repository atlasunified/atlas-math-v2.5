from __future__ import annotations

import itertools
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


def _poly_str(a=0,b=0,c=0,var='x'):
    terms=[]
    if a:
        if a==1: terms.append(f"{var}^2")
        elif a==-1: terms.append(f"-{var}^2")
        else: terms.append(f"{a}{var}^2")
    if b:
        s=f"{abs(b)}{var}" if abs(b)!=1 else var
        terms.append(("+" if b>0 else "-") + s)
    if c:
        terms.append(("+" if c>0 else "-") + str(abs(c)))
    if not terms: return '0'
    first=terms[0]
    out=first
    for t in terms[1:]:
        out += ' ' + t[0] + ' ' + t[1:]
    return out

MODULE_INFO = {"module_id": "algebra.polynomial_add_subtract_multiply", "name": "Polynomial Add, Subtract, Multiply", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 850, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"add_linear": 700}, "level_2": {"subtract_linear": 850}, "level_3": {"add_quadratic": 1000}, "level_4": {"multiply_monomial_binomial": 1200}, "level_5": {"multiply_binomial_binomial": 1400}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}


def _spec(family, values, problem, answer):
    canonical=':'.join([family]+[str(v) for v in values])
    return {"family":family,"values":values,"problem":problem,"answer":answer,"canonical_key":canonical,"case_id":canonical,"family_id":family}


def _sample_from_spec(spec,difficulty,instruction_idx=0):
    answer=spec['answer']
    metadata={"family":spec['family'],"level_number":_level_num(difficulty),"structured":True,"canonical_key":spec['canonical_key'],"case_id":spec['case_id'],"family_id":spec['family_id'],"template_id":spec['family'],"final_answer":answer,"values":list(spec.get('values',[]))}
    instruction=INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Simplify the polynomial expression", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emitted=0
    for a in range(-8,9):
        for b in range(-9,10):
            for c in range(-8,9):
                for d in range(-9,10):
                    p1=_poly_str(0,a,b); p2=_poly_str(0,c,d); ans=_poly_str(0,a+c,b+d)
                    yield _spec('add_linear',(a,b,c,d),f"Simplify ({p1}) + ({p2}).",ans)
                    emitted+=1
                    if emitted>=FAMILY_CAPS['level_1']['add_linear']: return

def iter_level2_specs():
    emitted=0
    for a in range(-8,9):
        for b in range(-9,10):
            for c in range(-8,9):
                for d in range(-9,10):
                    p1=_poly_str(0,a,b); p2=_poly_str(0,c,d); ans=_poly_str(0,a-c,b-d)
                    yield _spec('subtract_linear',(a,b,c,d),f"Simplify ({p1}) - ({p2}).",ans)
                    emitted+=1
                    if emitted>=FAMILY_CAPS['level_2']['subtract_linear']: return

def iter_level3_specs():
    emitted=0
    for a in range(-4,5):
        for b in range(-6,7):
            for c in range(-6,7):
                for d in range(-4,5):
                    for e in range(-6,7):
                        for f in range(-6,7):
                            ans=_poly_str(a+d,b+e,c+f)
                            yield _spec('add_quadratic',(a,b,c,d,e,f),f"Simplify ({_poly_str(a,b,c)}) + ({_poly_str(d,e,f)}).",ans)
                            emitted+=1
                            if emitted>=FAMILY_CAPS['level_3']['add_quadratic']: return

def iter_level4_specs():
    emitted=0
    for k in range(-8,9):
        if k==0: continue
        for b in range(-9,10):
            for c in range(-9,10):
                ans=_poly_str(0,k*b,k*c)
                yield _spec('multiply_monomial_binomial',(k,b,c),f"Simplify {k}({_poly_str(0,b,c)}).",ans)
                emitted+=1
                if emitted>=FAMILY_CAPS['level_4']['multiply_monomial_binomial']: return

def iter_level5_specs():
    emitted=0
    for a in range(-8,9):
        for b in range(-8,9):
            for c in range(-8,9):
                for d in range(-8,9):
                    x2=a*c
                    x1=a*d+b*c
                    x0=b*d
                    ans=_poly_str(x2,x1,x0)
                    yield _spec('multiply_binomial_binomial',(a,b,c,d),f"Simplify ({_poly_str(0,a,b)})({_poly_str(0,c,d)}).",ans)
                    emitted+=1
                    if emitted>=FAMILY_CAPS['level_5']['multiply_binomial_binomial']: return


def _iter_specs(difficulty='level_1'):
    level=_level_num(difficulty)
    if level==1:return _take(iter_level1_specs(),LEVEL_SPEC_CAPS['level_1'])
    if level==2:return _take(iter_level2_specs(),LEVEL_SPEC_CAPS['level_2'])
    if level==3:return _take(iter_level3_specs(),LEVEL_SPEC_CAPS['level_3'])
    if level==4:return _take(iter_level4_specs(),LEVEL_SPEC_CAPS['level_4'])
    return _take(iter_level5_specs(),LEVEL_SPEC_CAPS['level_5'])


def curriculum(): return {'level_1':['add linear polynomials'],'level_2':['subtract linear polynomials'],'level_3':['combine quadratic polynomials'],'level_4':['distribute a monomial across a binomial'],'level_5':['multiply two binomials']}

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


