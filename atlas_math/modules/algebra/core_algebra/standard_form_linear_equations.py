from __future__ import annotations

import itertools
import random
from fractions import Fraction
from typing import Iterable

from atlas_math.modules.shared.common import make_sample

INSTRUCTIONS = [
    "{instruction}: {problem}",
    "Solve and report the result: {problem}",
    "Work the problem and give the final answer: {problem}",
    "Compute the requested result: {problem}",
]

MAX_SPEC_PREFIX = 5000
MAX_GENERATE_MULTIPLIER = 8
MAX_ITER_SAMPLES = 4096


def _level_num(difficulty: str) -> int:
    try:
        value = int(str(difficulty).rsplit("_", 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str:
    return "|".join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


def _fmt_number(value) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    return str(value)

MODULE_INFO = {"module_id": "algebra.standard_form_linear_equations", "name": "Standard Form Linear Equations", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 600, "level_2": 800, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"slope_to_standard": 600}, "level_2": {"point_to_standard": 800}, "level_3": {"intercepts_to_standard": 1000}, "level_4": {"normalize_coefficients": 1200}, "level_5": {"convert_forms": 1400}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k,v in LEVEL_SPEC_CAPS.items()}

def _spec(family, values, problem, answer):
    canonical=':'.join([family]+[str(v) for v in values]); return {"family":family,"values":values,"problem":problem,"answer":answer,"canonical_key":canonical,"case_id":canonical,"family_id":family}

def _sample_from_spec(spec,difficulty,instruction_idx=0):
    answer=spec['answer']; metadata={"family":spec['family'],"level_number":_level_num(difficulty),"structured":True,"canonical_key":spec['canonical_key'],"case_id":spec['case_id'],"family_id":spec['family_id'],"template_id":spec['family'],"final_answer":answer,"values":list(spec.get('values',[]))}
    instruction=INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Write the equation in standard form", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)

def iter_level1_specs():
    emitted=0; limit=FAMILY_CAPS['level_1']['slope_to_standard']
    for m in [-5,-4,-3,-2,-1,1,2,3,4,5]:
        for b in range(-10,11):
            yield _spec('slope_to_standard',(m,b),f"Convert y = {m}x + {b} to standard form with integer coefficients and A > 0.",f"{-m}x + y = {b}" if -m>0 else f"{m}x - y = {-b}")
            emitted+=1
            if emitted>=limit:return

def iter_level2_specs():
    emitted=0; limit=FAMILY_CAPS['level_2']['point_to_standard']
    for m in [-4,-3,-2,-1,1,2,3,4]:
        for x1 in range(-5,6):
            for b in range(-8,9):
                y1=m*x1+b
                A=-m; B=1; C=y1-m*x1
                if A<0: A,B,C=-A,-B,-C
                yield _spec('point_to_standard',(m,x1,b),f"A line has slope {m} and passes through ({x1}, {y1}). Write it in standard form.",f"{A}x + {B}y = {C}")
                emitted+=1
                if emitted>=limit:return

def iter_level3_specs():
    emitted=0; limit=FAMILY_CAPS['level_3']['intercepts_to_standard']
    for x_int in range(1,11):
        for y_int in range(1,11):
            yield _spec('intercepts_to_standard',(x_int,y_int),f"Write the equation of the line with x-intercept {x_int} and y-intercept {y_int} in standard form.",f"{y_int}x + {x_int}y = {x_int*y_int}")
            emitted+=1
            if emitted>=limit:return

def iter_level4_specs():
    emitted=0; limit=FAMILY_CAPS['level_4']['normalize_coefficients']
    for A in range(1,8):
        for B in range(-7,8):
            if B==0: continue
            for C in range(-14,15):
                k=2
                yield _spec('normalize_coefficients',(A,B,C),f"Rewrite {k*A}x + {k*B}y = {k*C} in standard form with no common factor and A > 0.",f"{A}x + {B}y = {C}")
                emitted+=1
                if emitted>=limit:return

def iter_level5_specs():
    emitted=0; limit=FAMILY_CAPS['level_5']['convert_forms']
    for num in [-5,-4,-3,-2,-1,1,2,3,4,5]:
        for den in [2,3,4,5]:
            for b in range(-6,7):
                A=-num; B=den; C=b*den
                if A<0: A,B,C=-A,-B,-C
                yield _spec('convert_forms',(num,den,b),f"Convert y = {num}/{den}x + {b} to standard form with integer coefficients.",f"{A}x + {B}y = {C}")
                emitted+=1
                if emitted>=limit:return

def _iter_specs(difficulty='level_1'):
    level=_level_num(difficulty)
    if level==1:return _take(iter_level1_specs(),LEVEL_SPEC_CAPS['level_1'])
    if level==2:return _take(iter_level2_specs(),LEVEL_SPEC_CAPS['level_2'])
    if level==3:return _take(iter_level3_specs(),LEVEL_SPEC_CAPS['level_3'])
    if level==4:return _take(iter_level4_specs(),LEVEL_SPEC_CAPS['level_4'])
    return _take(iter_level5_specs(),LEVEL_SPEC_CAPS['level_5'])

def curriculum(): return {'level_1':['convert slope-intercept equations to standard form'],'level_2':['build standard form from point and slope'],'level_3':['use intercept information'],'level_4':['normalize standard-form coefficients'],'level_5':['convert fractional-slope equations to integer standard form']}
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


