from __future__ import annotations

import itertools
import random
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
        value = int(str(difficulty).rsplit('_', 1)[-1])
    except Exception:
        value = 1
    return max(1, min(5, value))


def _stable_seed(*parts) -> str:
    return '|'.join(str(p) for p in parts)


def _take(iterable: Iterable[dict], n: int) -> Iterable[dict]:
    for idx, item in enumerate(iterable):
        if idx >= max(0, int(n)):
            break
        yield item


MODULE_INFO = {"module_id": "algebra.arithmetic_sequences_explicit_recursive", "name": "Arithmetic Sequences: Explicit and Recursive", "topic": "algebra", "subtopic": "core_algebra", "difficulty_levels": ["level_1", "level_2", "level_3", "level_4", "level_5"], "enabled": True}
LEVEL_SPEC_CAPS = {"level_1": 700, "level_2": 850, "level_3": 1000, "level_4": 1200, "level_5": 1400}
FAMILY_CAPS = {"level_1": {"next_term": 700}, "level_2": {"explicit_value": 850}, "level_3": {"write_explicit": 1000}, "level_4": {"write_recursive": 1200}, "level_5": {"convert_between_forms": 1400}}
CAPACITY_HINTS = {k: {"value": v, "quality": "capped"} for k, v in LEVEL_SPEC_CAPS.items()}


def _spec(family, values, problem, answer):
    canonical=':'.join([family]+[str(v) for v in values])
    return {"family":family,"values":values,"problem":problem,"answer":answer,"canonical_key":canonical,"case_id":canonical,"family_id":family}


def _sample_from_spec(spec,difficulty,instruction_idx=0):
    answer=spec['answer']
    metadata={"family":spec['family'],"level_number":_level_num(difficulty),"structured":True,"canonical_key":spec['canonical_key'],"case_id":spec['case_id'],"family_id":spec['family_id'],"template_id":spec['family'],"final_answer":answer,"values":list(spec.get('values',[]))}
    instruction=INSTRUCTIONS[instruction_idx % len(INSTRUCTIONS)].format(instruction="Work with the arithmetic sequence", problem=spec['problem'])
    return make_sample(module_id=MODULE_INFO['module_id'], topic=MODULE_INFO['topic'], subtopic=MODULE_INFO['subtopic'], difficulty=difficulty, instruction=instruction, input_text=spec['problem'], answer=answer, metadata=metadata)


def iter_level1_specs():
    emitted=0
    for a1 in range(-20,21):
        for d in [-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9]:
            for n in range(4,9):
                seq=[a1+i*d for i in range(n)]
                yield _spec('next_term',(a1,d,n),f"The arithmetic sequence begins {', '.join(str(x) for x in seq)}. What is the next term?",str(a1+n*d))
                emitted+=1
                if emitted>=FAMILY_CAPS['level_1']['next_term']:
                    return


def iter_level2_specs():
    emitted=0
    for a1 in range(-15,16):
        for d in [-8,-6,-4,-3,-2,-1,1,2,3,4,6,8]:
            for n in range(5,26):
                ans=a1+(n-1)*d
                yield _spec('explicit_value',(a1,d,n),f"An arithmetic sequence has first term {a1} and common difference {d}. Find a_{n}.",str(ans))
                emitted+=1
                if emitted>=FAMILY_CAPS['level_2']['explicit_value']:
                    return


def iter_level3_specs():
    emitted=0
    for a1 in range(-12,13):
        for d in [-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7]:
            yield _spec('write_explicit',(a1,d),f"Write an explicit formula for the arithmetic sequence with first term {a1} and common difference {d}.",f"a_n = {a1} + (n - 1)({d})")
            emitted+=1
            if emitted>=FAMILY_CAPS['level_3']['write_explicit']:
                return


def iter_level4_specs():
    emitted=0
    for a1 in range(-15,16):
        for d in [-8,-6,-4,-3,-2,-1,1,2,3,4,6,8]:
            ans=f"a_1 = {a1}; a_n = a_(n-1) + ({d}) for n ≥ 2"
            yield _spec('write_recursive',(a1,d),f"Write a recursive definition for the arithmetic sequence with first term {a1} and common difference {d}.",ans)
            emitted+=1
            if emitted>=FAMILY_CAPS['level_4']['write_recursive']:
                return


def iter_level5_specs():
    emitted=0
    for a1 in range(-12,13):
        for d in [-7,-5,-4,-3,-2,-1,1,2,3,4,5,7]:
            explicit=f"a_n = {a1} + (n - 1)({d})"
            recursive=f"a_1 = {a1}; a_n = a_(n-1) + ({d}) for n ≥ 2"
            yield _spec('convert_between_forms',(a1,d),f"An arithmetic sequence has explicit formula {explicit}. Give an equivalent recursive definition.",recursive)
            emitted+=1
            if emitted>=FAMILY_CAPS['level_5']['convert_between_forms']:
                return


def _iter_specs(difficulty='level_1'):
    level=_level_num(difficulty)
    if level==1:return _take(iter_level1_specs(),LEVEL_SPEC_CAPS['level_1'])
    if level==2:return _take(iter_level2_specs(),LEVEL_SPEC_CAPS['level_2'])
    if level==3:return _take(iter_level3_specs(),LEVEL_SPEC_CAPS['level_3'])
    if level==4:return _take(iter_level4_specs(),LEVEL_SPEC_CAPS['level_4'])
    return _take(iter_level5_specs(),LEVEL_SPEC_CAPS['level_5'])


def curriculum(): return {'level_1':['find the next term of an arithmetic sequence'],'level_2':['evaluate arithmetic sequences from explicit parameters'],'level_3':['write explicit formulas'],'level_4':['write recursive formulas'],'level_5':['convert between explicit and recursive forms']}

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


