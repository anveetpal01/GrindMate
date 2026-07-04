# GrindMate Backend  -  Deep Study Guide (Hinglish)

> Ek Python fresher ke liye GrindMate ka **Django + DRF backend** ekdam zero se deep tak. Har chapter is repo ke **asli code** se padhaya gaya hai  -  generic tutorial nahi. Code padh, samajh, todh, dubara bana  -  yahi sabse fast tareeka hai backend mein solid hone ka.

**Naya hai? Seedha last chapter (Roadmap, Glossary & Interview Prep) se shuru kar**  -  wahan 'kis order me padho' likha hai. Phir Chapter 1 se sequence follow kar.

**Stack:** Django 5 · Django REST Framework · SimpleJWT · Celery · PostgreSQL (Neon) / SQLite · pytest + factory_boy + responses.


---

## Table of Contents

1. [Python Language Foundations (jo is codebase mein use hue hain)](#1-python-language-foundations-jo-is-codebase-mein-use-hue-hain)
2. [Project Setup & Settings Architecture (Django kaise boot hota hai)](#2-project-setup-settings-architecture-django-kaise-boot-hota-hai)
3. [Users App  -  Custom User, JWT Auth, Email Verification & Password Reset](#3-users-app-custom-user-jwt-auth-email-verification-password-reset)
4. [LeetCode App  -  Service Layer, External API Integration & Sync Orchestration](#4-leetcode-app-service-layer-external-api-integration-sync-orchestration)
5. [Groups App + Leaderboard  -  Django ORM Masterclass](#5-groups-app-leaderboard-django-orm-masterclass)
6. [Celery, Migrations, Caching & Testing (Supporting Cast)](#6-celery-migrations-caching-testing-supporting-cast)
7. [Ek Request ki Poori Journey (End-to-End Lifecycle)](#7-ek-request-ki-poori-journey-end-to-end-lifecycle)
8. [Study Roadmap, Glossary & Interview Prep Bank](#8-study-roadmap-glossary-interview-prep-bank)


---


## 1. Python Language Foundations (jo is codebase mein use hue hain)

Dekh bhai, yeh chapter thoda alag hai. Yahan hum Django ya DRF nahi padhenge  -  yahan hum **Python language** ki woh advanced cheezein padhenge jo is repo mein **actually use hui hain**. Generic tutorial nahi, GrindMate ka asli code. Har feature ke saath main tujhe `backend/apps/...` se real snippet dikhaunga, batauunga *kyun* use hua, aur *under the hood* kya ho raha hai. Chai bana le, shuru karte hain.

---

#### 1. Type hints + `from __future__ import annotations`

Pehle har file ki sabse upar yeh line dekh  -  `services.py`, `sync.py`, `managers.py`, `models.py`, `managers.py` (users)  -  **sab mein**:

```python
from __future__ import annotations
```

##### Type hints kya hai?

Type hint matlab tu function ke parameters aur return value ke saath ek "label" laga raha hai ki yeh kis type ka hoga. Dekh `sync.py` se:

```python
def upsert_problem(
 slug: str,
 *,
 client: LeetCodeClient | None = None,
 defer_meta: bool = False,
 fallback_title: str | None = None,
) -> Problem:
```

Yahan `slug: str` matlab "slug ek string hai", `-> Problem` matlab "yeh function ek `Problem` object return karega".

**Important baat:** Python in hints ko **runtime pe enforce nahi karta**. Agar tu `upsert_problem(123)` call kare (int de de string ki jagah), Python crash nahi karega type-check pe. Yeh hints sirf:
- **Tujhe aur IDE ko** batate hain (autocomplete, red squiggly lines).
- **Type checkers** (mypy, pyright) ke liye hain jo CI mein chalte hain.
- **Documentation** ki tarah kaam karte hain  -  function signature dekh ke samajh aata hai kya andar jaayega.

##### `str | None` union syntax

```python
ranking: int | None
fallback_title: str | None = None
error: str | None = None
```

`int | None` ka matlab  -  "yeh value ya toh `int` hogi, ya `None`". Pipe `|` yahan "ya/or" jaisa hai. Purane Python (3.9 se pehle) mein yeh aise likhna padta tha:

```python
from typing import Optional
ranking: Optional[int] # purana tareeka  -  same baat
```

Naya `int | None` (Python 3.10+) cleaner hai. Is project mein 3.10+ chal raha hai isliye naya syntax use hua hai har jagah.

##### Ab `from __future__ import annotations` ka asli khel  -  under the hood

Yeh line **sabse important** hai samajhne ke liye. Default Python mein, jab interpreter function definition padhta hai, woh type hints ko **turant evaluate** karta hai (eager evaluation). Matlab `client: LeetCodeClient | None` likha hai toh Python `LeetCodeClient` naam ko us waqt resolve karne ki koshish karega.

Problem yeh aati hai `managers.py` mein. Dekh:

```python
class SubmissionLogQuerySet(models.QuerySet):
 def for_user(self, user: AbstractBaseUser) -> SubmissionLogQuerySet:
 return self.filter(user=user)
```

Yahan `for_user` ka return type `SubmissionLogQuerySet` hai  -  **jis class ko hum abhi define kar rahe hain!** Class ka body chal raha hai, class abhi poori bani nahi hai, aur hum usi class ka naam return type mein use kar rahe hain. Bina `from __future__ import annotations` ke, Python yahan `NameError: name 'SubmissionLogQuerySet' is not defined` de deta (kyunki naam abhi class namespace mein aaya hi nahi).

**`from __future__ import annotations` kya karta hai:** Yeh saare type hints ko **string** bana deta hai (lazy evaluation). Matlab `-> SubmissionLogQuerySet` ko Python `-> "SubmissionLogQuerySet"` ki tarah treat karta hai  -  bas ek string store kar leta hai, evaluate nahi karta. Resolve tabhi hota hai jab koi tool (mypy, ya `typing.get_type_hints()`) explicitly maange.

Isi wajah se `managers.py` mein yeh pattern bhi chalta hai:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
 from django.contrib.auth.models import AbstractBaseUser
```

`TYPE_CHECKING` ek constant hai jo **runtime pe hamesha `False`** hoti hai, lekin type checker (mypy/pyright) ke liye `True` maani jaati hai. Toh `AbstractBaseUser` ka import sirf type-checking ke time hota hai, runtime pe nahi. Fayda  -  circular imports avoid hote hain aur startup thoda fast rehta hai. Aur kyunki `from __future__ import annotations` lagi hai, `user: AbstractBaseUser` waala hint string ban gaya, toh runtime pe woh import na hone se bhi kuch nahi tootega.

> **Gotcha:** Agar tu `from __future__ import annotations` use kar raha hai, toh tu hints ko **runtime pe directly nahi padh sakta** as real classes  -  woh strings hain. Pydantic ya kuch frameworks jo runtime pe hints padhte hain, unke saath dhyan rakhna padta hai. Django models ke field types is se affected nahi hote (woh hints nahi hain, woh actual `models.CharField(...)` objects hain).

---

#### 2. `@dataclass(frozen=True)`  -  DTOs banane ka saaf tareeka

`services.py` mein dekh, teen DTO (Data Transfer Object) define hue hain:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ProfileSummary:
 handle: str
 ranking: int | None
 total_solved: int
 easy_solved: int
 medium_solved: int
 hard_solved: int


@dataclass(frozen=True)
class RecentSolve:
 title_slug: str
 title: str
 solved_at: datetime  # tz-aware UTC


@dataclass(frozen=True)
class ProblemMeta:
 title_slug: str
 title: str
 difficulty: str
 topic_tags: list[str]
 is_premium: bool
 leetcode_id: int | None
```

##### `@dataclass` karta kya hai?

`@dataclass` ek decorator hai jo tere likhe class attributes (jo type hints ke saath declare kiye) ko dekh ke **automatically `__init__`, `__repr__`, `__eq__` jaise dunder methods generate kar deta hai**. Matlab tujhe yeh boilerplate nahi likhna:

```python
# @dataclass ke bina yeh sab haath se likhna padta:
class ProfileSummary:
 def __init__(self, handle, ranking, total_solved, easy_solved, medium_solved, hard_solved):
 self.handle = handle
 self.ranking = ranking
 # ... har field ke liye self.x = x
 def __repr__(self):
 return f"ProfileSummary(handle={self.handle!r}, ...)"
 def __eq__(self, other):
 # field by field compare...
```

Yeh sab `@dataclass` ek line mein de deta hai. Tu sirf banake use karta hai:

```python
return ProfileSummary(
 handle=matched["username"],
 ranking=(matched.get("profile") or {}).get("ranking"),
 total_solved=counts.get("all", 0),
 ...
)
```

##### `frozen=True` ka matlab

`frozen=True` matlab object banne ke baad uski koi field **change nahi ho sakti**  -  woh immutable hai.

```python
summary = ProfileSummary(handle="anveet", ranking=5000, ...)
summary.ranking = 1 # ❌ raises dataclasses.FrozenInstanceError
```

##### Kyun frozen use kiya?

Yeh DTOs **read-only data carriers** hain  -  LeetCode se aaya data ek jagah se doosri jagah le jaane ke liye. Dekh `sync.py` mein `_apply_summary` kaise use karta hai:

```python
def _apply_summary(account: LeetCodeAccount, summary) -> None:
 account.handle = summary.handle
 account.ranking = summary.ranking
 account.total_solved = summary.total_solved
 ...
```

`summary` sirf **padha** ja raha hai, modify nahi. `frozen=True` is intent ko *enforce* karta hai  -  galti se koi `summary.total_solved = 0` na kar de. Immutable objects ka ek aur fayda: woh **hashable** ho jaate hain (set/dict key ban sakte hain), aur multi-threaded ya retry-heavy code mein safe hote hain kyunki state badal hi nahi sakti.

##### Frozen vs normal `@dataclass`  -  `SyncResult` ka case

Ab dekh `sync.py` mein `SyncResult` **frozen nahi** hai:

```python
@dataclass
class SyncResult:
 new_solves: int
 total_solved: int
 problems_resolved: int
 error: str | None = None
```

Yeh deliberate design decision hai. Lekin yahan dhyan de: `error: str | None = None`  -  yeh ek **default value** hai. Dataclass mein, **default-wale fields hamesha bina-default-wale fields ke baad aane chahiye** (bilkul function arguments jaise). `new_solves`, `total_solved`, `problems_resolved` ke koi default nahi, isliye `__init__` mein woh required hain; `error` optional hai.

##### Kab dataclass, kab normal class?

| Use case | Kya use karein |
|---|---|
| Sirf data carry karna (DTO, config) | `@dataclass(frozen=True)` |
| Data + thodi behaviour, mutable | `@dataclass` |
| Bahut saari custom methods, complex logic | normal class |
| DB row | Django model (dataclass nahi) |

> **Gotcha:** Mutable default mat de directly  -  `topic_tags: list[str] = []` ❌. Yeh saare instances ke beech *shared* ho jaata hai (classic Python trap). Dataclass mein `field(default_factory=list)` use karte hain. Is repo mein `ProblemMeta.topic_tags` ka koi default nahi rakha (hamesha pass hota hai), isliye trap se bach gaye.

---

#### 3. `@property`, `@classmethod`, `@staticmethod`

##### `@property`  -  method ko attribute jaisa banana

`models.py` (users) mein:

```python
class User(AbstractBaseUser, PermissionsMixin):
 ...
 @property
 def name(self) -> str:
 return self.display_name or self.username
```

`@property` decorator ek method ko aisa bana deta hai ki tu usko **bina brackets ke** access kare, ek normal attribute jaise:

```python
user.name # ✅ aise  -  koi () nahi
user.name() # ❌ ye galat  -  'str' object is not callable
```

**Under the hood:** `@property` ek "descriptor" banata hai. Jab tu `user.name` likhta hai, Python attribute lookup ke time dekhta hai ki `name` ek property descriptor hai, aur uska `__get__` chala ke andar wala function (`return self.display_name or self.username`) run kar ke result deta hai.

**Kyun use kiya?** `name` koi stored column nahi hai DB mein  -  yeh computed hai (`display_name` agar set hai toh woh, warna `username`). Property se yeh "fake attribute" ban gaya jo har baar fresh compute hota hai, bina DB mein extra column banaye. Caller ko pata bhi nahi chalta ki yeh stored hai ya computed  -  yeh **encapsulation** hai.

> Note: Is project ke jo files maine padhe, unme `LeetCodeAccount.is_verified` property ya `get_token` classmethod literally nahi dikhe  -  woh shayad doosri files/branch mein honge. Toh main yahan **is repo mein jo actually maujood hai** uske examples de raha hun (`User.name` property, aur neeche `UserManager` ke methods), taaki tu galat code memorize na kare.

##### `@classmethod` vs `@staticmethod` vs normal method  -  fark

Yeh teeno is project mein `managers.py` (users) jaise jagah ke around clear hote hain. Concept samajh le:

```python
class Example:
 def instance_method(self): # `self` = object instance
 ...
 @classmethod
 def class_method(cls): # `cls` = class itself
 ...
 @staticmethod
 def static_method(): # na self, na cls  -  bas namespacing
 ...
```

- **Instance method**  -  `self` milta hai, object ki state access karta hai. Jaise `User.__str__(self)`.
- **`@classmethod`**  -  pehla argument `cls` (class khud) hota hai, instance nahi. Factory methods ke liye perfect. Django ka `BaseUserManager` aur Django ke `from_queryset` is pattern par bane hain.
- **`@staticmethod`**  -  na `self` na `cls`. Yeh basically ek normal function hai jise class ke andar rakha gaya hai logical grouping ke liye.

Is repo ka best real example **classmethod-style factory** `managers.py` (leetcode) mein hai:

```python
class SubmissionLogManager(models.Manager.from_queryset(SubmissionLogQuerySet)):
 def get_queryset(self) -> SubmissionLogQuerySet:
 return SubmissionLogQuerySet(self.model, using=self._db)
```

`models.Manager.from_queryset(...)`  -  yeh `from_queryset` ek **classmethod** hai jo Django ke andar baithi hai. Yeh `SubmissionLogQuerySet` ke saare methods (`for_user`, `this_week`, `by_difficulty`) ko ek naya Manager class mein copy kar ke deta hai. `cls` (yani `Manager`) pe kaam karke ek **naya class** banaya  -  yeh classmethod ka classic use (factory that returns a class/instance).

`compute_streaks` (same file) ek **module-level function** hai, kisi class ke andar nahi:

```python
def compute_streaks(distinct_dates: list[date]) -> tuple[int, int]:
 ...
```

Decision: yeh pure logic hai (dates → streaks), ismein kisi object ki state ki zaroorat nahi. Toh isko `@staticmethod` class ke andar daalne ki bhi zaroorat nahi pari  -  seedha module function bana diya. Yeh ek seekh hai: **agar function ko `self`/`cls` chahiye hi nahi, toh use class ke andar mat ghuso**  -  module-level function aur saaf hota hai aur test karna aasan.

---

#### 4. Decorators  -  actually hota kya hai?

Decorator ka matlab hai: ek function (ya class) jo **doosre function ko leke, usko wrap kar ke, ek naya behaviour-wala function return karta hai**. `@decorator` syntax bas shortcut hai.

```python
@retry(...)
def query(self, ...):
 ...

# yeh exactly iske barabar hai:
def query(self, ...):
 ...
query = retry(...)(query)
```

Matlab `query` ab original function nahi raha  -  woh `retry(...)` ke andar lipta hua naya function hai jo pehle retry logic chalata hai, phir original ko call karta hai.

##### Repo mein decorators kahan kahan

**`@retry` (tenacity library)**  -  `services.py`:

```python
from tenacity import (
 retry,
 retry_if_exception_type,
 stop_after_attempt,
 wait_exponential,
)

class LeetCodeClient:
 @retry(
 retry=retry_if_exception_type(LeetCodeRateLimited),
 stop=stop_after_attempt(3),
 wait=wait_exponential(multiplier=1, min=2, max=10),
 reraise=True,
 )
 def query(self, query: str, variables: dict) -> dict:
 ...
 if response.status_code in (429, 403):
 raise LeetCodeRateLimited(...)
```

Padh ke samajh kya ho raha hai:
- `retry=retry_if_exception_type(LeetCodeRateLimited)`  -  sirf `LeetCodeRateLimited` exception aane par retry karo (baaki errors pe nahi).
- `stop=stop_after_attempt(3)`  -  max 3 koshish.
- `wait=wait_exponential(multiplier=1, min=2, max=10)`  -  har retry ke beech wait badhta jaayega: 2s, 4s, 8s... (max 10s). Isko **exponential backoff** kehte hain  -  rate-limited server ko saans dene ka time.
- `reraise=True`  -  agar 3 koshish ke baad bhi fail, toh asli exception fenk do (tenacity ka apna wrapper exception nahi).

**Yeh `@retry` decorator ka pure power hai:** `query` method ke andar **ek line bhi retry logic nahi hai**. Saara retry/backoff/wait `@retry` wrapper handle kar raha hai. Method sirf apna kaam karta hai  -  request bhejo, error pe `raise` karo. Yeh **separation of concerns** ka beautiful example hai.

`@retry` ka concept yeh hai  -  woh tere `query` ko ek loop mein wrap karta hai jo roughly aisa dikhta hai:

```python
def wrapped_query(*args, **kwargs):
 for attempt in range(3):
 try:
 return original_query(*args, **kwargs)
 except LeetCodeRateLimited:
 if attempt == 2:
 raise
 sleep(backoff_time) # 2s, 4s, 8s
```

**`@receiver` (Django signals)**, **`@shared_task` (Celery)**, aur DRF ke decorators bhi isi principle pe chalte hain  -  woh tere function ko leke usko ek system ke saath "register" karte hain ya extra behaviour dete hain. (Inka detailed code Django/Celery chapters mein aayega; yahan bas concept clear rakh: **decorator = function ko wrap/register karne ka tareeka**.)

> **Gotcha:** Decorator function ki identity badal deta hai. Bina `functools.wraps` ke, wrapped function ka `__name__` aur docstring kho jaate hain. tenacity/Celery jaise mature libraries `functools.wraps` use karte hain isliye `query.__name__` abhi bhi `"query"` hi rehta hai. Apna decorator likhe toh `@functools.wraps(func)` lagana mat bhulna.

---

#### 5. Exception classes & inheritance hierarchy

`services.py` ke top par dekh:

```python
class LeetCodeAPIError(Exception):
 """Raised when LeetCode's API returns a non-recoverable error."""


class LeetCodeRateLimited(LeetCodeAPIError):
 """Raised on 429 / Cloudflare blocks - caller should back off."""


class LeetCodeUserNotFound(LeetCodeAPIError):
 """Raised when the username doesn't resolve to a real LeetCode user."""
```

Yeh ek **exception hierarchy** hai:

```
Exception
└-- LeetCodeAPIError (base  -  koi bhi LeetCode error)
 ├-- LeetCodeRateLimited (specifically rate limit / 429 / 403)
 └-- LeetCodeUserNotFound  (specifically user na mile)
```

##### Custom exceptions kyun banate?

Standard `Exception` raise karne ke bajaye apni classes banane ke 3 bade fayde, aur teeno is repo mein practically use hue hain:

**Fayda 1  -  Specific cheez pe retry, generic pe nahi.** Yaad hai upar `@retry` mein?

```python
retry=retry_if_exception_type(LeetCodeRateLimited)
```

Sirf `LeetCodeRateLimited` pe retry hota hai. Agar `LeetCodeUserNotFound` aaya (galat username), toh retry karna bekaar hai  -  username toh retry karne se sahi nahi hoga! Alag-alag exception class hone se retry logic **selectively** kaam kar paata hai.

**Fayda 2  -  Base class se ek saath sab catch karo.** Dekh `sync.py`:

```python
try:
 summary = fetch_profile_summary(account.handle, client=client)
 recent = fetch_recent_solves(account.handle, client=client)
except LeetCodeAPIError as exc:
 return _record_failure(account, exc)
```

Yahan `except LeetCodeAPIError` likha hai  -  aur kyunki `LeetCodeRateLimited` aur `LeetCodeUserNotFound` dono uske **children** hain, **teeno** is `except` mein pakde jaate hain. Yeh inheritance ka kamaal hai  -  base class catch karo, saare subtypes automatic aa gaye. Agar bilkul rate-limit-specific handling chahiye toh tu `except LeetCodeRateLimited` pehle likh sakta hai, phir `except LeetCodeAPIError`.

**Fayda 3  -  Network error ko bhi domain error mein convert.** `services.py`:

```python
try:
 response = self.session.post(...)
except requests.RequestException as exc:
 raise LeetCodeAPIError(f"Network error talking to LeetCode: {exc}") from exc
```

Yahan `requests` library ka `RequestException` pakda, aur usko apne `LeetCodeAPIError` mein convert kar diya. Iska fayda  -  `sync.py` ko `requests` library ke baare mein kuch jaanne ki zaroorat nahi. Woh sirf `LeetCodeAPIError` handle karta hai. Service layer ne implementation detail (requests) ko **hide** kar diya.

##### `raise ... from exc` ka matlab

```python
raise LeetCodeAPIError(...) from exc
```

`from exc` Python ko batata hai  -  "yeh naya exception us `exc` ki wajah se aaya". Traceback mein dono dikhte hain: *"The above exception was the direct cause of the following exception"*. Debugging mein gold  -  original network error chhupta nahi.

> **Gotcha:** Empty exception class banane ke liye sirf `pass` ya docstring kaafi hai (jaise repo mein docstring hai). `__init__` likhne ki zaroorat nahi  -  `Exception` ka default `__init__` message string le leta hai.

---

#### 6. Context managers  -  `with` block

##### `with transaction.atomic():`  -  sync.py

```python
with transaction.atomic():
 for solve in recent:
 problem = Problem.objects.filter(title_slug=solve.title_slug).first()
 if problem is None:
 problem = upsert_problem(solve.title_slug, defer_meta=True, ...)
 problems_resolved += 1
 _log, created = SubmissionLog.objects.get_or_create(...)
 if created:
 new_solves += 1

 _apply_summary(account, summary)
 account.save()
```

##### `with` karta kya hai under the hood?

`with X:` block ke liye `X` ko ek **context manager** hona chahiye  -  matlab uske paas do dunder methods hon: `__enter__` aur `__exit__`. Jab tu `with X:` likhta hai:

1. Block shuru hone par Python `X.__enter__()` call karta hai (setup).
2. Block ka code chalta hai.
3. Block khatam hone par  -  **chahe normally khatam ho ya exception se**  -  Python `X.__exit__()` call karta hai (cleanup).

`transaction.atomic()` ke case mein:
- `__enter__` → DB transaction shuru karta hai (BEGIN / savepoint).
- Block ke andar saare DB writes ek group ban jaate hain.
- Agar block bina error ke poora hua → `__exit__` **COMMIT** karta hai (sab ek saath save).
- Agar block ke andar koi exception aaya → `__exit__` **ROLLBACK** karta hai (sab undo).

**Kyun zaroori hai yahan?** `sync_account` ek loop mein bahut saari rows banata hai (`SubmissionLog`, `Problem`) aur phir `account.save()` karta hai. Agar beech mein kuch fail ho jaaye, toh **aadha-adhura data** DB mein nahi rehna chahiye. `transaction.atomic()` guarantee deta hai: **ya toh sab save ho, ya kuch bhi nahi** (atomicity  -  "A" of ACID). `with` ki khoobsurti  -  tujhe try/except/commit/rollback manually nahi likhna; context manager khud `__exit__` mein decide kar leta hai.

##### `requests.Session()`  -  services.py

```python
class LeetCodeClient:
 def __init__(self, *, timeout: float = 10.0):
 ...
 self.session = requests.Session()
 self.session.headers.update({...})
```

`requests.Session()` bhi ek context manager hai (`with requests.Session() as s:` bhi likh sakte hain). Lekin yahan ise `with` mein nahi, **instance attribute** ki tarah rakha gaya hai  -  kyunki `LeetCodeClient` apni poori life mein kai requests karta hai aur Session ko reuse karna chahta hai.

**Session kyun?** Har `requests.get/post` naya TCP + TLS handshake karta hai (slow). `Session` ek **connection pool** rakhta hai  -  same host (`leetcode.com`) ke liye connection reuse hota hai, headers ek baar set ho jaate hain. Dekh, headers ek hi baar set hue:

```python
self.session.headers.update({
 "Content-Type": "application/json",
 "User-Agent": ("Mozilla/5.0 (compatible; GrindMateSync/1.0; ...)"),
 "Referer": "https://leetcode.com",
})
```

Aur phir har query mein `self.session.post(...)`  -  yeh saare headers automatic lag jaate hain. (Note: comment bhi bata raha hai  -  *"LeetCode rejects the default python-requests user-agent"*  -  isliye custom UA zaroori hai.)

> **Gotcha:** Class docstring bolti hai *"Construct one per task / request - it's stateless aside from the session."* Matlab ek `LeetCodeClient` ko bahut der tak / multiple threads mein share mat karo. Session thread-safe poori tarah guarantee nahi, aur per-task naya client banana saaf rehta hai.

---

#### 7. Enums via `models.TextChoices`

`sync.py` import karta hai `SyncStatus` aur use karta hai:

```python
from .models import LeetCodeAccount, Problem, SubmissionLog, SyncStatus

# ...
account.sync_status = SyncStatus.OK # success
account.sync_status = SyncStatus.FAILED # failure
```

`SyncStatus` ek `models.TextChoices` enum hai (definition `leetcode/models.py` mein hai). Concept yeh hai  -  Django ke `TextChoices` se tu DB ke liye ek **string-based enum** banata hai:

```python
class SyncStatus(models.TextChoices):
 OK = "ok", "OK"
 FAILED = "failed", "Failed"
 PENDING = "pending", "Pending"
```

Har member ke do hisse: pehla (`"ok"`) = **DB mein jo store hoga**; doosra (`"OK"`) = **human-readable label** (admin/forms mein dikhega). `gettext_lazy` se label translate bhi ho sakta hai.

##### Kyun raw strings ki jagah enum?

Tu `account.sync_status = "failed"` bhi likh sakta tha. Par phir:
- Typo ka risk  -  `"failde"` likh diya toh koi error nahi, silently galat data.
- IDE autocomplete nahi.
- Refactor mushkil  -  string change karna ho toh poore codebase mein dhoondho.

`SyncStatus.FAILED` likhne se  -  typo pe IDE turant pakdega (`AttributeError`), autocomplete milega, aur ek hi jagah (enum definition) source of truth banti hai.

##### Under the hood

`models.TextChoices` actually Python ke built-in `enum.Enum` + Django ki extra magic ka combo hai. `SyncStatus.OK` ek enum member hai, lekin woh **`str` ki tarah bhi behave karta hai** (kyunki TextChoices `str` se inherit karta hai). Isliye `account.sync_status = SyncStatus.OK` DB mein `"ok"` store ho jaata hai bina manual `.value` likhe. Aur `SyncStatus.choices` automatically `[("ok", "OK"), ("failed", "Failed"), ...]` deta hai jo model field ke `choices=` mein jaata hai.

Tere prompt mein `Difficulty` aur `GroupMembership` roles ka zikr hai  -  woh bhi yahi pattern follow karte hain. `models.py` (users) mein `GroupMembership.ROLE_ADMIN` is style ka mil bhi raha hai `delete()` ke andar:

```python
.filter(role=GroupMembership.ROLE_ADMIN)
```

Aur `SubmissionLog.SOURCE_AUTO` (sync.py):

```python
defaults={"source": SubmissionLog.SOURCE_AUTO},
```

Yeh constants (`ROLE_ADMIN`, `SOURCE_AUTO`) bhi same philosophy  -  magic strings ko named constants se replace karo.

---

#### 8. Comprehensions & generators

##### List comprehension  -  services.py

```python
topic_tags=[t["slug"] for t in (q.get("topicTags") or [])],
```

Padh: "har `t` ke liye jo `topicTags` list mein hai, `t["slug"]` nikaalo, aur unki ek nayi list banao". Yeh same baat for-loop mein 4 line leti:

```python
tags = []
for t in (q.get("topicTags") or []):
 tags.append(t["slug"])
```

Comprehension ek line mein, fast bhi (Python internally optimize karta hai), aur readable.

##### Dict comprehension  -  services.py

```python
counts = {
 row["difficulty"].lower(): row["count"]
 for row in matched["submitStats"]["acSubmissionNum"]
}
```

`{key: value for item in iterable}`  -  yeh **dict comprehension** hai. LeetCode se aaye rows (har row mein `difficulty` aur `count`) ko ek `{difficulty: count}` dict mein badal diya. Phir aise use hota hai:

```python
total_solved=counts.get("all", 0),
easy_solved=counts.get("easy", 0),
```

`.get("all", 0)`  -  agar `"all"` key nahi mili toh `0` (default). Yeh data ko ek lookup-friendly shape mein laana  -  comprehension ka perfect use.

##### `values_list`  -  managers.py (lazy, generator-jaisa)

```python
def by_difficulty(self) -> dict[str, int]:
 rows = (
 self.values("problem__difficulty")
 .annotate(n=Count("id"))
 .values_list("problem__difficulty", "n")
 )
 return dict(rows)
```

`values_list("problem__difficulty", "n")` ORM se tuples ki ek **lazy** iterable deta hai  -  `[("easy", 12), ("medium", 5), ...]`. `dict(rows)` use seedha `{"easy": 12, "medium": 5}` mein convert kar deta hai. Yahan key insight  -  `values_list` ka result QuerySet hai jo **iterate hone tak DB query fire nahi karta**. `dict(rows)` jab iterate karta hai, tab actual SQL chalta hai. (Yeh laziness wala detail ORM chapter mein deep jaayega.)

`flat=True` waala variant bhi same file mein:

```python
.values_list("d", flat=True)
```

`flat=True` matlab single column ko tuple `(x,)` ke andar nahi, seedha `x` deta hai  -  `[date1, date2, ...]` na ki `[(date1,), (date2,)]`.

##### `itertools.pairwise`  -  compute_streaks (managers.py)

Yeh sabse pyara example hai. Streak nikalne ke liye consecutive dates compare karne hote hain. Naive tareeka  -  index pe loop, `dates[i]` aur `dates[i-1]`. Par yeh cleaner hai:

```python
from itertools import pairwise

sorted_asc = sorted(set(distinct_dates))
longest = run = 1
for prev, curr in pairwise(sorted_asc):
 if curr - prev == timedelta(days=1):
 run += 1
 longest = max(longest, run)
 else:
 run = 1
```

`pairwise([a, b, c, d])` deta hai → `(a, b), (b, c), (c, d)`  -  har consecutive **jodi**. Toh `for prev, curr in pairwise(...)` har step pe pichla aur abhi wala date deta hai. Agar fark exactly 1 din (`timedelta(days=1)`), toh streak `run += 1`, warna `run = 1` se reset.

**`pairwise` ek generator hai**  -  woh poori list of pairs memory mein nahi banata, ek-ek jodi *on the fly* yield karta hai. Bade data pe memory efficient.

Dhyan de yeh chhoti line bhi:

```python
longest = run = 1
```

Yeh **chained assignment**  -  dono `longest` aur `run` ko ek saath `1` set kiya. (Lekin yeh int ke liye safe hai; mutable objects  -  jaise list  -  ke saath `a = b = []` mat karna, dono *same* list ko point karenge.)

`set()` ka use  -  `sorted(set(distinct_dates))`  -  duplicates hata ke unique dates, phir sort. Set ka kaam yahan dedup karna.

---

#### 9. `*args, **kwargs`

`models.py` (users) ka `delete` override sabse saaf example hai:

```python
def delete(self, *args, **kwargs):
 ...
 # ownership transfer logic ...
 return super().delete(*args, **kwargs)
```

##### Kya hote hain `*args` aur `**kwargs`?

- `*args`  -  saare **positional** arguments ko ek **tuple** mein pakad leta hai.
- `**kwargs`  -  saare **keyword** arguments ko ek **dict** mein pakad leta hai.

```python
def f(*args, **kwargs):
 print(args) # tuple
 print(kwargs)  # dict

f(1, 2, x=3, y=4)
# args = (1, 2)
# kwargs = {'x': 3, 'y': 4}
```

##### Yahan kyun use kiya?

`User.delete` Django ke base `Model.delete()` ko **override** kar raha hai (pehle owned groups transfer karta hai, phir asli delete). Django `delete()` ko internally kabhi `using=...`, `keep_parents=...` jaise arguments ke saath call kar sakta hai. Hum nahi chahte ki override karte waqt un sab arguments ko explicitly likhna pade (aur agar Django future mein naye add kare toh hamara code toot jaaye).

Toh `*args, **kwargs` se hum jo bhi aaya **as-is pakad ke `super().delete(*args, **kwargs)` ko aage pass kar dete hain**. Yeh "pass-through" pattern hai  -  apna extra kaam karo, baaki parent ko jo mila woh waise hi de do.

Yahan `*args, **kwargs` ko unpack karke pass karna  -  yeh **reverse operation** hai. Definition mein `*` collect karta hai; call mein `*` spread/unpack karta hai. `super().delete(*args, **kwargs)` matlab "jo tuple/dict pakda tha, usko wapas individual arguments mein khol ke parent ko de do".

Project mein `_create_user` (users/managers.py) bhi `**extra_fields` se yeh karta hai:

```python
def _create_user(self, email, password, **extra_fields):
 ...
 user = self.model(email=email, **extra_fields)
```

Caller `create_user(email, password, username="x", timezone="Asia/Kolkata")` bhejta hai, `username` aur `timezone` `extra_fields` dict mein aa jaate hain, aur `self.model(email=email, **extra_fields)` se woh User constructor mein keyword arguments ban ke chale jaate hain. Flexible  -  naya field add karo, signature change nahi karna padta.

##### Bonus: keyword-only arguments (`*` akela)

Repo mein yeh pattern bahut hai  -  dekh `services.py`:

```python
def __init__(self, *, timeout: float = 10.0):
def fetch_profile_summary(handle: str, *, client: LeetCodeClient | None = None):
def upsert_problem(slug: str, *, client=None, defer_meta=False, fallback_title=None):
```

Akela `*` (bina naam ke) signature mein likhne ka matlab  -  **uske baad ke saare arguments keyword-only ho jaate hain**. Matlab `fetch_profile_summary("anveet", some_client)` ❌ allowed nahi; `fetch_profile_summary("anveet", client=some_client)` ✅ likhna padega. Yeh **deliberate** hai  -  caller ko force karta hai ki woh `client=`, `defer_meta=` naam ke saath likhe, taaki code padhne wale ko turant samajh aaye kya pass ho raha hai. Boolean `defer_meta=True` bina naam ke `True` likhna confusing hota  -  keyword-only isse rokta hai.

---

#### 10. Truthiness, `is None` vs `== None`, `or` default pattern

##### Truthiness

Python mein har value ko boolean context (`if`, `or`, `and`) mein **truthy** ya **falsy** maana jaata hai. Falsy hain: `None`, `False`, `0`, `0.0`, `""` (empty string), `[]` (empty list), `{}` (empty dict), `set()`. Baaki sab truthy.

Dekh `services.py`:

```python
matched = data.get("matchedUser")
if not matched:
 raise LeetCodeUserNotFound(...)
```

`if not matched`  -  agar `matched` `None` hai **ya** empty dict `{}` hai, dono case mein truthy nahi, toh error. Yeh ek check mein dono conditions cover kar gaya.

##### `is None` vs `== None`

Yeh **interview ka favourite** sawaal hai. Repo `is None` use karta hai (sahi tareeka)  -  `sync.py`:

```python
problem = Problem.objects.filter(title_slug=solve.title_slug).first()
if problem is None:
 problem = upsert_problem(...)
```

Aur `users/models.py`:

```python
if replacement is None:
 ...
```

**`is` vs `==` ka fark:**
- `is` → **identity** check. "Kya yeh bilkul wahi object hai?" (memory mein same address). `None` Python mein **singleton** hai  -  poore program mein `None` ka ek hi object hota hai. Toh `x is None` exactly sahi check hai.
- `==` → **equality** check, jo `__eq__` method call karta hai. Koi object apna `__eq__` override karke `== None` ko `True` bana sakta hai (galti se ya jaan ke), ya `__eq__` mein exception bhi de sakta hai. Isliye `None` ke liye `==` use karna risky aur slow hai.

**Rule:** `None`, `True`, `False` ke saath hamesha `is` / `is not` use karo. Repo mein bhi consistently yahi hai  -  `if problem is None`, `if replacement is None`, aur `is_usable` mein `self.used_at is None` (users/models.py).

##### `or` default pattern

Yeh pattern repo mein **bahut** baar aaya  -  sabse important Python idiom. `sync.py` aur `services.py`:

```python
client = client or LeetCodeClient()
```

Yeh padh: "agar `client` truthy hai toh `client` use karo; warna (yani `None` aaya) ek naya `LeetCodeClient()` bana ke use karo."

**Under the hood:** Python ka `or` "short-circuit" karta hai aur **operand return karta hai, boolean nahi**. `A or B` → agar `A` truthy hai toh `A` return, warna `B` return. Toh:
- `client=None` aaya → `None or LeetCodeClient()` → `None` falsy hai → `LeetCodeClient()` banta hai.
- `client=<some client>` aaya → woh truthy → seedha wahi return, naya nahi banta.

**Kyun yeh pattern?** Yeh **dependency injection** ke liye hai. Normal use mein function khud client bana leta hai. Lekin **testing** mein tu apna fake/mock client `client=mock` pass kar sakta hai, aur tab function asli LeetCode ko call nahi karega. Yeh design `fetch_profile_summary`, `fetch_recent_solves`, `fetch_problem_meta`, `verify_account`, `sync_account`  -  sab mein consistent hai. Testability ke liye sona.

`name` property mein bhi same idiom (users/models.py):

```python
return self.display_name or self.username
```

"`display_name` agar set hai (non-empty) toh woh, warna `username`."

Aur nested `or` with safe navigation  -  `services.py`:

```python
ranking=(matched.get("profile") or {}).get("ranking"),
```

Yeh thoda chतुर hai: `matched.get("profile")` agar `None` aaya, toh `None.get("ranking")` crash karta. Isliye `(matched.get("profile") or {})`  -  agar profile `None`/falsy hai toh empty dict `{}` use karo, phir `.get("ranking")` safe se `None` de dega. Yeh **"or {} guard"** pattern hai  -  `AttributeError` se bachne ka clean tareeka.

> **Gotcha:** `or` default pattern tab dhokha de sakta hai jab valid value bhi **falsy** ho. Misaal: `limit = limit or 50`  -  agar koi jaan-boojh ke `limit=0` bhejna chahe, toh `0` falsy hai aur `50` ban jaayega! Aise case mein `limit if limit is not None else 50` ya keyword default (`limit: int = 50`, jo `fetch_recent_solves` mein use hua) behtar hai. Yahi reason hai `fetch_recent_solves` ne `or` ke bajaye signature default `limit: int = 50` rakha.

---

#### 11. f-strings aur `__str__`

##### f-strings

f-string = `f"..."`  -  string ke andar `{}` mein expression likh ke value embed karna. Repo mein har jagah:

```python
# services.py
raise LeetCodeUserNotFound(f"No LeetCode user found for handle {handle!r}.")
raise LeetCodeAPIError(f"Network error talking to LeetCode: {exc}")
raise LeetCodeRateLimited(f"Rate limited (HTTP {response.status_code}).")
```

`{handle}` jagah pe `handle` ki value aa jaati hai. **Important detail:** `{handle!r}` mein `!r` conversion flag hai  -  yeh `repr(handle)` call karta hai (str nahi). Fark:

```python
handle = "anveet"
f"{handle}" # -> anveet
f"{handle!r}"  # -> 'anveet' (quotes ke saath)
```

`!r` error messages mein useful  -  quotes se saaf dikhta hai value kahan shuru/khatam hui (whitespace, empty string spot karne mein madad). Isliye user-input wale values (`handle`, `title_slug`) ke error messages mein `!r` use hua hai. Dekh `sync.py` mein bhi:

```python
raise LeetCodeAPIError(f"Problem {title_slug!r} not found.")
```

Slicing f-string ke andar  -  `users/models.py`:

```python
return f"token for {self.user.username} ({self.token[:8]}…)"
```

`{self.token[:8]}`  -  token ke pehle 8 chars hi dikhaye (poora secret token log/admin mein expose na ho). Security ke liye accha touch.

> **f-string vs logging  -  ek bada gotcha:** Dekh `sync.py` mein logging f-string se **nahi** hua:
> ```python
> logger.warning("LeetCode call failed for %s: %s", account.handle, exc)
> ```
> Yahan jaan-boojh ke purana `%s` style use hua, `f"...{account.handle}..."` nahi. Kyun? Logging mein agar `warning` level disabled ho, toh f-string toh **fir bhi** string banata (waste of work), jabki `%s` style mein formatting **tabhi** hoti hai jab message actually log hota hai (lazy). Isliye **logging mein hamesha `%s` placeholders, baaki har jagah f-strings.** Yeh ek senior-level distinction hai jo interview mein bonus marks dilata hai.

##### `__str__` dunder

`__str__` ek "dunder" (double-underscore) method hai jo batata hai ki object ko **string mein kaise convert karna** hai  -  `str(obj)`, `print(obj)`, ya admin/template mein display ke time yeh chalta hai.

`users/models.py`:

```python
class User(...):
 def __str__(self) -> str:
 return self.username or self.email
```

```python
class EmailVerificationToken(models.Model):
 def __str__(self) -> str:
 return f"token for {self.user.username} ({self.token[:8]}…)"
```

**Kyun?** Django admin, shell, logs  -  sab jagah jab object print hota hai toh by default `<User: User object (1)>` jaisa bekaar dikhta hai. `__str__` define karne se `<User: anveet>` dikhega  -  human-friendly. `User.__str__` mein `or` pattern bhi  -  username na ho toh email.

> **`__str__` vs `__repr__`:** `__str__` end-user ke liye (readable), `__repr__` developer ke liye (debugging, ideally unambiguous  -  `repr()` aur shell mein dikhta hai). Dataclasses (`ProfileSummary` etc.) ko `@dataclass` automatically ek accha `__repr__` de deta hai  -  `ProfileSummary(handle='anveet', ranking=5000, ...)`  -  isliye DTOs pe alag se `__str__` likhne ki zaroorat nahi padi.

---

#### Common galtiyan / gotchas  -  ek jagah

1. **`from __future__ import annotations` na lagana** jab forward-reference (`-> SubmissionLogQuerySet` apni hi class mein) use ho raha ho → `NameError`.
2. **Mutable default in dataclass** (`topic_tags: list = []`) → saare instances share karenge. `field(default_factory=list)` use karo.
3. **`== None`** likhna → `is None` use karo, hamesha.
4. **`x or default`** jab `x=0`/`""`/`[]` valid ho → galat default lag jaayega. `is None` check ya signature default use karo.
5. **Logging mein f-string** → `%s` placeholders use karo (lazy evaluation, performance).
6. **frozen dataclass ki field set karne ki koshish** → `FrozenInstanceError`. Naya object banao.
7. **Custom decorator bina `functools.wraps`** → wrapped function ka `__name__`/docstring kho jaata hai.
8. **`requests` bina Session** har baar → naya TCP/TLS handshake, slow. Session reuse karo.

---

#### Interview Questions + short answers

**Q1. `from __future__ import annotations` kya karta hai aur kyun chahiye?**
Saare type annotations ko string bana deta hai (lazy evaluation), turant evaluate nahi karta. Isse forward references (class apni hi return type mein), circular imports, aur `TYPE_CHECKING`-only imports kaam karte hain bina `NameError` ke.

**Q2. `@dataclass(frozen=True)` aur normal class mein fark?**
`@dataclass` `__init__`/`__repr__`/`__eq__` auto-generate karta hai. `frozen=True` instance immutable bana deta hai (fields set nahi ho sakte) aur hashable bhi. Read-only DTOs (jaise `ProfileSummary`) ke liye ideal jahan accidental mutation rokna ho.

**Q3. `is None` vs `== None`  -  kya use karein aur kyun?**
`is None`. `None` singleton hai, `is` identity check karta hai (fast, reliable). `==` `__eq__` call karta hai jo override ho sakta hai ya exception de sakta hai  -  risky.

**Q4. `client = client or LeetCodeClient()` line samjhao.**
`or` short-circuit karke operand return karta hai. Agar `client` truthy (pass kiya gaya) toh wahi, warna naya banao. Yeh dependency injection ka pattern hai  -  tests mein mock client inject karne deta hai.

**Q5. Custom exception hierarchy (`LeetCodeAPIError` → `LeetCodeRateLimited`/`LeetCodeUserNotFound`) ka kya fayda?**
Base class catch karne se saare subtypes ek `except` mein aa jaate hain; specific subtype pe selective handling (jaise sirf rate-limit pe retry) bhi ho jaati hai. Domain errors ko library errors (jaise `requests.RequestException`) se decouple karta hai.

**Q6. Decorator hota kya hai? `@retry` ka example do.**
Ek function jo doosre function ko wrap karke naya behaviour deta hai. `@retry` `query` method ko ek retry-loop mein wrap karta hai  -  `LeetCodeRateLimited` aane par exponential backoff ke saath max 3 baar retry, bina method ke andar koi retry code likhe.

**Q7. `*args` aur `**kwargs` ka use `User.delete` override mein kyun?**
Parent `delete()` ko jo bhi arguments mile (`using`, `keep_parents` etc.) unhe as-is pass-through karne ke liye  -  `super().delete(*args, **kwargs)`. Isse Django future mein naye args add kare toh bhi override nahi tootega.

**Q8. Logging mein f-string kyun avoid karte hain?**
`logger.warning("...%s", val)` lazy hai  -  string tabhi banti hai jab message actually log hota hai. f-string hamesha pehle string bana deta, disabled log level pe bhi  -  wasted work. Performance + best practice.

**Q9. `models.TextChoices` enum raw string se behtar kyun?**
Type safety (typo pe `AttributeError`), IDE autocomplete, single source of truth, aur DB value + human label dono ek jagah. `SyncStatus.OK` likhne se `"failde"` jaise silent bugs nahi aate.

**Q10. `with transaction.atomic():` block exception aane par kya karta hai?**
Context manager ka `__exit__` exception detect karke poora transaction **ROLLBACK** kar deta hai  -  koi aadhi-adhuri row save nahi rehti. Bina exception ke `__exit__` COMMIT karta hai. Atomicity guarantee.

---

#### Khud try kar (exercises)

1. **Default pitfall reproduce kar:** Ek chhota script likh jisme `def f(limit=None): return limit or 50`. Ise `f(0)` se call kar aur dekh kya return hota hai (`50` aayega!). Phir `limit if limit is not None else 50` se theek kar. `fetch_recent_solves` ne `or` ke bajaye signature default `limit: int = 50` kyun rakha  -  isse connect kar.

2. **frozen dataclass tod ke dekh:** Python shell mein `ProfileSummary` import kar (`from apps.leetcode.services import ProfileSummary`), ek instance bana, phir `summary.ranking = 1` set karne ki koshish kar. `FrozenInstanceError` aayega. Phir `@dataclass(frozen=True)` ko sirf `@dataclass` kar ke wahi test repeat kar  -  ab set ho jaayega. Dono behaviours note kar.

3. **`pairwise` apne haath se likh:** `compute_streaks` mein `from itertools import pairwise` use hua. Tu `itertools` import kiye bina apna `def my_pairwise(seq):` likh (hint: generator + `yield (prev, curr)`), aur `compute_streaks` ke longest-streak loop ko apne version se chala ke verify kar ki same answer aata hai. Generator `yield` aur `return` ka fark bhi note kar.


---


## 2. Project Setup & Settings Architecture (Django kaise boot hota hai)

Dekh bhai, har Django project ke do hisse hote hain: **ek "config" wala dimaag** (`grindmate/` folder  -  settings, urls, wsgi/asgi) aur **"feature" wale apps** (`apps/users`, `apps/leetcode`, `apps/groups`). Is chapter mein hum sirf dimaag ko samjhenge  -  jab tu `python manage.py runserver` maarta hai, andar exactly kya-kya hota hai, settings 4 files mein kyun toot ke padi hai, aur production-grade config kya hoti hai. Yeh foundation hai; iske baad models/views/serializers padhega toh sab jaga fit baithega.

GrindMate ka backend layout aisa hai:

```
backend/
├-- manage.py # dev CLI entry point
├-- grindmate/ # project "config" package
│ ├-- settings/
│ │ ├-- base.py # shared config  -  sab kuch yahan
│ │ ├-- development.py # local dev overrides
│ │ ├-- production.py # prod overrides (strict + secure)
│ │ └-- test.py # test overrides (fast, in-memory)
│ ├-- urls.py # root URL router
│ ├-- wsgi.py # prod sync server entry
│ └-- asgi.py # prod async server entry
├-- apps/ # actual features
│ ├-- users/
│ ├-- leetcode/
│ └-- groups/
└-- requirements/
 └-- base.txt
```

---

#### 1. Boot Sequence  -  `manage.py` se le ke pehli request tak

##### `manage.py` kya karta hai

Yeh dev/CLI ka entry point hai. Iska kaam basically **ek environment variable set karna** aur baaki Django ko de dena.

```python
# backend/manage.py
def main() -> None:
 os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grindmate.settings.development")
 from django.core.management import execute_from_command_line
 execute_from_command_line(sys.argv)
```

Ek-ek line samajh:

- `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grindmate.settings.development")`  -  yeh line bolti hai: "agar `DJANGO_SETTINGS_MODULE` already set nahi hai, toh use development par set kar do." `setdefault` important hai  -  yeh **override nahi karta** agar already set ho. Matlab CI/CD mein agar tu `DJANGO_SETTINGS_MODULE=grindmate.settings.test` export kar de, toh manage.py usko respect karega, apna development nahi thopega. **Yahi reason hai ki dev ko default rakha**  -  `manage.py` mostly developer apne laptop pe chalata hai, prod par toh gunicorn `wsgi.py` chalata hai (jiska default production hai, aage dekhenge).

- `execute_from_command_line(sys.argv)`  -  yeh Django ka management command dispatcher hai. `sys.argv` matlab tune jo terminal pe type kiya (`["manage.py", "runserver"]` ya `["manage.py", "migrate"]`). Yeh argv ko parse karke sahi command class dhoondhta hai aur chalata hai.

`DJANGO_SETTINGS_MODULE` ek **dotted Python path** hai  -  `grindmate.settings.development` matlab file `grindmate/settings/development.py`. Django isko `importlib` se import karta hai aur uske saare UPPERCASE module-level variables ko `django.conf.settings` object par chipka deta hai. Isiliye tu poore codebase mein `from django.conf import settings; settings.DEBUG` likh sakta hai  -  woh actually is file ko padh raha hota hai.

##### Boot ki poori chain (under the hood)

Jab `runserver`/`gunicorn` start hota hai, yeh sequence chalti hai:

```
1. DJANGO_SETTINGS_MODULE env var read hoti hai
2. django.setup() call hota hai, jo:
 a. settings module import karta hai (base.py top-to-bottom execute)
 b. apps.populate(INSTALLED_APPS)  -  har app ka AppConfig load,
 models register, app.ready() call
 c. logging config apply
3. URLconf (ROOT_URLCONF = "grindmate.urls") import hoti hai
4. Server request ke liye ready
```

Yahan ek critical baat: **settings file ek normal Python file hai jo top-to-bottom execute hoti hai.** Matlab `base.py` mein jo bhi likha hai  -  `env("DATABASE_URL")`, `dj_database_url.parse(...)`  -  yeh sab **import time pe ek baar chalta hai**, per-request nahi. Isiliye settings mein heavy/slow cheez nahi daalte.

`apps.populate()` step pe app ka order matter karta hai  -  woh point 5 mein detail mein.

##### WSGI vs ASGI  -  yeh kya bala hai

Tere app ka Python code aur web server (gunicorn, nginx)  -  beech mein ek standard "contract" chahiye taaki koi bhi server kisi bhi framework ko chala sake. Woh contract hai **WSGI** (Web Server Gateway Interface).

```python
# backend/grindmate/wsgi.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grindmate.settings.production")
application = get_wsgi_application()
```

- `application` ek **callable** hai. WSGI spec bolti hai: server ko ek aisa function/object do jo `application(environ, start_response)` signature le. `environ` ek dict hai (request ke headers, path, method sab), `start_response` ek callback hai response status/headers bhejne ke liye.
- **Gunicorn isko aise uthata hai:** `gunicorn grindmate.wsgi:application`. Yeh string `module:variable` format mein hai  -  gunicorn `grindmate.wsgi` module import karta hai aur usme se `application` naam ka variable nikaalta hai. Bas. Har incoming HTTP request ke liye gunicorn `application(environ, start_response)` call karta hai, Django response banata hai, gunicorn HTTP par bhej deta hai.

Notice kar  -  `wsgi.py` ka default `production` hai, `development` nahi. **Kyun?** Kyunki `wsgi.py` ko sirf production server (gunicorn) hi import karta hai. Developer toh `manage.py runserver` chalata hai (jo dev settings deta hai). Yeh ek deliberate split hai  -  production environment galti se dev settings se boot na ho jaaye.

**ASGI** WSGI ka async bada bhai hai. WSGI ek request = ek synchronous call, ek thread block. WSGI websockets, long-lived connections, ya `async def` views handle nahi kar sakta. ASGI kar sakta hai.

```python
# backend/grindmate/asgi.py
"""ASGI entry point - for future websockets / async views."""
application = get_asgi_application()
```

Comment khud bolta hai  -  abhi GrindMate websockets use nahi karta, par file ready hai. Kal ko "live leaderboard update" feature aaya toh ASGI server (uvicorn/daphne) pe switch kar sakte. Yeh **forward-thinking structure** hai, par over-engineering nahi  -  sirf 8-line file rakhi hai.

**Gotcha:** Naye log `runserver` ko production server samajh lete hain. `runserver` sirf development ke liye hai  -  single-threaded-ish, auto-reload wala, **kabhi prod mein mat chalana**. Prod mein hamesha gunicorn (WSGI) chalta hai.

---

#### 2. Settings Split Pattern  -  ek file kyun nahi, 4 kyun

Naya banda sochta hai "ek `settings.py` mein `if DEBUG:` daal dete hain na, kaam ho jayega." Galat. GrindMate **12-Factor App** principle follow karta hai  -  config code se alag, aur environment ke hisaab se alag.

Structure yeh hai:

```
base.py # SAARI shared config (apps, middleware, DRF, JWT, logging...)
  ↑ from .base import *
  ├-- development.py # dev: DEBUG=True, LocMem cache, eager celery
  ├-- production.py # prod: DEBUG=False, security headers, Sentry
  └-- test.py # test: in-memory DB, fast password hasher
```

Har env-specific file ki **pehli line** yeh hoti hai:

```python
# development.py / production.py / test.py  -  sabki pehli line
from .base import *  # noqa: F403
```

`from .base import *` ka matlab  -  base.py ke saare UPPERCASE names (DEBUG, INSTALLED_APPS, MIDDLEWARE, REST_FRAMEWORK, env, sab) is namespace mein le aao. Phir neeche jo bhi re-assign karega, woh **override** ho jayega. Yeh "inheritance via import" hai  -  OOP class inheritance nahi, par effect same: base = parent, env file = child jo selectively override karta hai.

> `# noqa: F403`  -  yeh ruff/flake8 ke linter ko bolta hai "is wildcard import pe complain mat kar, jaanbujh ke kiya hai." Aur env files mein tu `# noqa: F405` dekhega  -  F405 matlab "yeh naam undefined lag raha hai, shayad wildcard import se aaya." Linter ko pata nahi `env` ya `LOGGING` kahan se aaya kyunki woh `*` import se aaye. Isiliye suppress karte.

**Kyun split? (real reasons)**

| Problem agar single file | Split se solution |
|---|---|
| Dev secrets aur prod secrets ek jaga, galti se commit | base mein koi secret nahi, env-specific overrides |
| `if DEBUG: ... else: ...` ki bhulbhulaiya | clean  -  dev file padh, dev ka behavior pata |
| Test ke liye DB slow (Postgres) | test.py mein in-memory SQLite force |
| Prod par DEBUG=True bhool gaye = security disaster | prod.py mein `DEBUG = False` hard-coded |

**Har env exactly kya override karta hai:**

`development.py`:
```python
DEBUG = True
INSTALLED_APPS += ["django_extensions"] # sirf dev tooling
ALLOWED_HOSTS = ["*"] # localhost pe relaxed
CORS_ALLOW_ALL_ORIGINS = True # Vite proxy ke liye
EMAIL_BACKEND = "...console.EmailBackend"  # email terminal pe print
# Redis optional  -  default LocMem cache
# Celery eager  -  task turant same process mein chalta
LOGGING["root"]["level"] = "DEBUG" # zyada verbose
```

`production.py`:
```python
DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY") # default NAHI  -  must be set
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # default NAHI
# + saare security headers (SSL redirect, HSTS...)
# + Sentry init
# + apps logger ko INFO (DEBUG nahi  -  noise kam)
# + Redis na ho toh LocMem fallback
```

`test.py`:
```python
DATABASES = {"default": {"ENGINE": "...sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["...MD5PasswordHasher"]  # tez, secure nahi  -  par test mein chalega
CACHES = LocMem
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = "...locmem.EmailBackend" # email memory mein, assert kar sakte
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {astronomically high}}
```

Ek **design subtlety** test.py mein dekh  -  woh `REST_FRAMEWORK` ko poora replace nahi karta, balki `{**REST_FRAMEWORK, ...}` se **merge** karta hai:

```python
REST_FRAMEWORK = {
 **REST_FRAMEWORK,  # base ka poora dict spread karo
 "DEFAULT_THROTTLE_RATES": {  # sirf yeh key override
 "anon": "100000/hour", ...
 },
}
```

`**REST_FRAMEWORK` base ka pura dict spread karta hai, phir `DEFAULT_THROTTLE_RATES` key ko overwrite. Result  -  auth classes, pagination sab base wale rehte, sirf throttle rates effectively disable. **Agar simple `REST_FRAMEWORK = {...}` likhta toh baaki saari config gayab ho jaati.** Yeh chhoti baat hai par yahi portfolio-grade detail hai.

**Throttle test mein disable kyun?** Kyunki test suite ek user ke 50 requests seconds mein maarta hai  -  real throttle rate `60/hour` test ko `429 Too Many Requests` se fail kar dega. Isiliye rate `100000/hour` kar diya  -  effectively off.

---

#### 3. `django-environ`  -  config ko environment se kaise padhte hain

Hard-coded values code mein? Bilkul nahi. GrindMate `django-environ` use karta hai:

```python
# base.py
import environ
env = environ.Env()
env_file = BASE_DIR / ".env"
if env_file.exists():
 env.read_env(env_file)
```

- `env = environ.Env()`  -  ek reader object banata hai.
- `env.read_env(env_file)`  -  `.env` file (key=value lines) padh ke `os.environ` mein load karta hai. `if env_file.exists()` check zaroori hai  -  prod mein `.env` file hoti hi nahi (waha real OS env vars set hote, Render/Railway dashboard se), toh exists() False return karega aur crash nahi hoga.

Phir typed readers:

```python
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")  # string
DEBUG = env.bool("DJANGO_DEBUG", default=False) # bool
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])  # CSV list
EMAIL_PORT = env.int("EMAIL_PORT", default=587) # int
```

**Yeh typing kyun zaroori hai?** Environment variables hamesha **strings** hoti hain. `.env` mein `DJANGO_DEBUG=False` likha toh OS use string `"False"` deta. Aur Python mein `bool("False")` ka result `True` hai (non-empty string truthy hota)! Yeh classic bug hai. `env.bool()` smart hai  -  `"False"`, `"0"`, `"no"`, `"off"` ko `False` samajhta. `env.int()` `"587"` ko integer `587` banata. `env.list()` `"a,b,c"` ko `["a", "b", "c"]` mein split karta.

##### Priority: OS env var > `.env` file (yeh user ne literally face kiya tha)

Yeh **galti se baar-baar pakadta hai**, isliye dhyaan se. `env()` resolve karne ka order:

```
1. OS environment variable (asli os.environ)  -  HIGHEST
2. .env file ki value (jo read_env ne load ki)
3. code mein diya default=  -  LOWEST
```

Real scenario jo user ne face kiya: tu `.env` mein `DATABASE_URL=postgres://localhost/grindmate` likhta hai, par tere shell mein pehle se `DATABASE_URL` export hai (shayad kisi aur project se, ya CI se). Tu sochta "main toh .env mein local DB diya hai", par app **OS wali value** uthati hai  -  kyunki `read_env` by default already-set OS vars ko **overwrite nahi karta**. Result: "maine .env change kiya par effect nahi aa raha." Debug karte time `os.environ.get("DATABASE_URL")` print karke confirm kar  -  agar wahan kuch hai, woh `.env` ko jeet raha hai.

**Mental model:** `.env` sirf "defaults agar OS mein kuch na ho" deta hai. OS env hamesha boss hai. Yeh actually **feature** hai (12-factor)  -  prod par platform real env vars inject karta hai, woh `.env` (jo waha hoti bhi nahi) ko jeet jaate hain.

---

#### 4. `dj-database-url`  -  ek string se poora DB config

Postgres connection settings 5 alag keys (HOST, PORT, NAME, USER, PASSWORD) mein dena painful hai. Modern platforms (Render, Railway, Heroku) ek single `DATABASE_URL` env var dete hain. `dj-database-url` usko parse karta hai.

```python
# base.py
import dj_database_url  # noqa: E402

_db_url = env("DATABASE_URL", default="")
if _db_url:
 DATABASES = {"default": dj_database_url.parse(_db_url, conn_max_age=600)}
else:
 DATABASES = {
 "default": {
 "ENGINE": "django.db.backends.sqlite3",
 "NAME": BASE_DIR / "db.sqlite3",
 }
 }
```

- `DATABASE_URL` jaise: `postgres://user:pass@host:5432/dbname`. `dj_database_url.parse()` isko Django ka `DATABASES["default"]` dict (ENGINE, NAME, USER, PASSWORD, HOST, PORT) mein tod deta hai. Ek line, zero manual config.
- **SQLite fallback logic:** `if _db_url:`  -  agar `DATABASE_URL` set hai (prod), Postgres use karo. Warna (local dev) SQLite file. **Yeh dev convenience hai**  -  naye contributor ko Postgres install/configure karne ki zaroorat nahi, `git clone` → `migrate` → chal pada SQLite par. Prod par platform `DATABASE_URL` deta hai toh apne aap Postgres switch.
- `conn_max_age=600`  -  **connection pooling/reuse**. By default Django har request ke baad DB connection close kar deta hai (`conn_max_age=0`). Naya connection kholna mehenga hai (TCP handshake + auth, ~tens of ms). `600` matlab "ek connection ko 600 seconds tak reuse karo." Prod mein yeh latency aur DB load dono kam karta. **Gotcha:** `conn_max_age` ke saath agar DB server idle connection ko apni taraf se close kar de toh "stale connection" errors aate  -  par 600s reasonable hai aur Django 5.x mein health-check bhi hai.

`# noqa: E402`  -  import file ke top par nahi, beech mein hai (paths setup ke baad). E402 "module import not at top" warning hai, deliberate hai isliye suppress.

---

#### 5. `INSTALLED_APPS`  -  teen baalti mein kyun banta

```python
DJANGO_APPS = [
 "django.contrib.admin", "django.contrib.auth",
 "django.contrib.contenttypes", "django.contrib.sessions",
 "django.contrib.messages", "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
 "rest_framework", "rest_framework_simplejwt",
 "rest_framework_simplejwt.token_blacklist",
 "corsheaders", "django_filters",
 "django_celery_beat", "django_celery_results",
]
LOCAL_APPS = ["apps.users", "apps.leetcode", "apps.groups"]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
```

**Yeh split sirf readability ke liye hai**  -  Django ko parwah nahi, woh final `INSTALLED_APPS` list dekhta. Par human ke liye instantly clear: "yeh Django ka built-in, yeh pip se aaya, yeh humne likha." Naya banda 2 second mein samajh jaaye project ka surface area.

**App order kyun matter karta hai (yeh real hai, sirf cosmetic nahi):**

1. **App registry population**  -  `apps.populate()` is order mein har app ka `AppConfig.ready()` chalata. Agar app A app B ke signals/models par depend karta hai, order galat ho toh load fail ya silent bug.
2. **Template/static override**  -  Django pehle wali app ko priority deta jab same-named template/static dhoondhta. Built-in admin ke templates ko apne app se override karna ho toh apni app pehle daalni padti.
3. **Management commands & migrations dependency**  -  `django.contrib.contenttypes` aur `auth` pehle aate kyunki baaki apps inke models (ContentType, Permission) par foreign keys rakhte. Inhe pehle migrate hona zaroori.
4. **`token_blacklist`** alag app hai  -  yeh JWT refresh token blacklist ke models deta. Iske bina `BLACKLIST_AFTER_ROTATION=True` (point 8) kaam nahi karega kyunki blacklist table hi nahi banegi.

**Gotcha:** `AUTH_USER_MODEL = "users.User"` (base.py line 108)  -  GrindMate custom user model use karta hai. Iska **golden rule**: custom user model **first migration se pehle** define hona chahiye. Project shuru hote hi yeh decide karo, baad mein switch karna nightmare hai (saare FKs `auth.User` par point kar chuke honge).

---

#### 6. `MIDDLEWARE`  -  onion model, order is everything

Middleware ek **layered pipeline** hai. Har request neeche jaati hai (list mein top-to-bottom), view hit karti hai, phir response upar wapas aati hai (bottom-to-top). Isko **onion model** bolte  -  har layer ke do moments: ek "request andar aate waqt", ek "response bahar jaate waqt."

```python
MIDDLEWARE = [
 "django.middleware.security.SecurityMiddleware", # 1
 "whitenoise.middleware.WhiteNoiseMiddleware", # 2
 "corsheaders.middleware.CorsMiddleware", # 3
 "django.contrib.sessions.middleware.SessionMiddleware", # 4
 "django.middleware.common.CommonMiddleware", # 5
 "django.middleware.csrf.CsrfViewMiddleware", # 6
 "django.contrib.auth.middleware.AuthenticationMiddleware",# 7
 "django.contrib.messages.middleware.MessageMiddleware", # 8
 "django.middleware.clickjacking.XFrameOptionsMiddleware", # 9
]
```

Visual:

```
Request  →  [Security] → [WhiteNoise] → [CORS] → [Session] → ... → VIEW
 ↓
Response ←  [Security] ← [WhiteNoise] ← [CORS] ← [Session] ← ... ← VIEW
```

Har ek kya karta:

| # | Middleware | Kaam |
|---|---|---|
| 1 | **SecurityMiddleware** | SSL redirect, HSTS header, content-type-nosniff. **Sabse upar** taaki insecure request ko view tak pahunchne se pehle hi redirect/reject kare. |
| 2 | **WhiteNoiseMiddleware** | Static files (CSS/JS) directly Django se serve. Security ke turant baad  -  taaki static file request ko aage ke heavy middleware (session, auth) na chalana pade. |
| 3 | **CorsMiddleware** | Cross-origin headers (`Access-Control-Allow-Origin`). **Jaldi** rakha  -  kyunki preflight `OPTIONS` request ko CSRF/auth se pehle hi sahi CORS headers ke saath jawab dena padta. corsheaders ki docs khud bolti "as high as possible." |
| 4 | **SessionMiddleware** | `request.session` available karta. **Auth se pehle** zaroori, kyunki auth session par depend karta. |
| 5 | **CommonMiddleware** | URL normalization (trailing slash `APPEND_SLASH`), `Content-Length` set. |
| 6 | **CsrfViewMiddleware** | CSRF token validate (POST/PUT/DELETE pe). |
| 7 | **AuthenticationMiddleware** | `request.user` set karta (session se). **Session ke baad** hona zaroori. |
| 8 | **MessageMiddleware** | Django messages framework (flash messages). |
| 9 | **XFrameOptionsMiddleware** | `X-Frame-Options` header  -  clickjacking se bachao. |

**Order galat hone ka real example:** Agar `AuthenticationMiddleware` ko `SessionMiddleware` se **upar** rakh de, toh auth middleware `request.session` access karega jo abhi exist hi nahi karta → `AttributeError`. Isiliye Django docs ye order recommend karti, aur GrindMate exactly follow karta.

**Note:** Yeh sab **DRF/JWT auth se alag hai.** DRF ka `JWTAuthentication` (point 7) per-view authentication hai, jo middleware ke **baad** view ke andar chalti. `AuthenticationMiddleware` Django ke session-based `request.user` ke liye hai (mainly admin panel). Donon coexist karte.

---

#### 7. `REST_FRAMEWORK` block  -  DRF ka global brain

Yeh ek dict hai jo **poore project ki DRF default behavior** set karta. Har API view jab tak khud override na kare, yeh defaults use karega.

```python
REST_FRAMEWORK = {
 "DEFAULT_AUTHENTICATION_CLASSES": (
 "rest_framework_simplejwt.authentication.JWTAuthentication",
 "rest_framework.authentication.SessionAuthentication",
 ),
 "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
 "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
 "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
 "PAGE_SIZE": 25,
 "DEFAULT_THROTTLE_CLASSES": (
 "rest_framework.throttling.AnonRateThrottle",
 "rest_framework.throttling.UserRateThrottle",
 ),
 "DEFAULT_THROTTLE_RATES": {
 "anon": "60/hour",
 "user": "1000/hour",
 "register": "10/hour",
 "verify_email": "20/hour",
 "password_reset": "5/hour",
 "resend_verification": "5/hour",
 },
}
```

Iske field-by-field:

- **`DEFAULT_AUTHENTICATION_CLASSES`**  -  har request pe DRF yeh classes try karta, order mein. Pehle `JWTAuthentication` (`Authorization: Bearer <token>` header dekhta). Agar woh fail/absent, `SessionAuthentication` (cookie-based  -  yeh admin/browsable API ke liye). Pehli jo succeed kare, `request.user` set kar deti. **JWT pehle kyun?** Kyunki API clients (React frontend) JWT bhejte; session sirf browser-based admin ke liye fallback.
- **`DEFAULT_PERMISSION_CLASSES`**  -  `IsAuthenticated` default. Matlab **har endpoint by default login chahta** ("secure by default"). Jo public hone chahiye (register, login)  -  woh views khud `permission_classes = [AllowAny]` lagati hain. Yeh ulta approach (default open, kuch close) se **safer** hai  -  bhulne par endpoint locked rehta, leaked nahi.
- **`DEFAULT_FILTER_BACKENDS`**  -  `DjangoFilterBackend` se URL query params (`?status=solved`) se queryset filter kar sakte, declaratively.
- **`DEFAULT_PAGINATION_CLASS` + `PAGE_SIZE: 25`**  -  list endpoints automatically `?page=2` support karenge, ek page mein 25 items. Yeh **bahut important**  -  bina pagination ke 10,000-row list ek hi response mein bhej dena DB aur frontend dono maar dega.
- **`DEFAULT_THROTTLE_CLASSES` + `RATES`**  -  rate limiting. `AnonRateThrottle` (logged-out user, IP-based) `60/hour`, `UserRateThrottle` (logged-in, user-id based) `1000/hour`. Plus **named scopes**: `register: 10/hour` matlab koi spam-register na kare, `password_reset: 5/hour` brute-force/email-bombing rokta. Yeh named rates un views se judti hain jo `throttle_scope = "register"` set karti.

**Yeh dict globally kaise apply hota?** DRF ka har `APIView`/`ViewSet` initialize hote waqt `api_settings` object padhta, jo internally is `REST_FRAMEWORK` dict ko `django.conf.settings` se uthata. View jab tak class-level attribute (`permission_classes = [...]`) se override na kare, yeh global default use hota. Ek jaga config, poore project pe asar  -  **DRY**.

---

#### 8. `SIMPLE_JWT` block  -  token lifecycle

```python
SIMPLE_JWT = {
 "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MIN", default=15)),
 "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
 "ROTATE_REFRESH_TOKENS": True,
 "BLACKLIST_AFTER_ROTATION": True,
 "AUTH_HEADER_TYPES": ("Bearer",),
 "USER_ID_FIELD": "id",
 "USER_ID_CLAIM": "user_id",
}
```

JWT (JSON Web Token)  -  ek signed token jo user ki identity carry karta, server pe session store kiye bina. Do tarah ke tokens:

- **Access token**  -  short-lived (`15 min`). Har API request mein bheja jaata. Choti life isliye ki agar leak ho jaaye toh 15 min mein bekaar.
- **Refresh token**  -  long-lived (`7 days`). Sirf naya access token lene ke liye. Access expire ho toh frontend refresh token bhej ke naya access leta  -  user ko dobara login nahi karna padta.

- **`ROTATE_REFRESH_TOKENS: True`**  -  jab refresh token use hota naya access lene ke liye, toh **naya refresh token bhi milta** (purana invalid). Yeh security badhata  -  refresh token bhi rotate hote rehte, ek leaked refresh token zyada der useful nahi.
- **`BLACKLIST_AFTER_ROTATION: True`**  -  rotate hone par purana refresh token **blacklist** ho jaata (DB mein "ab valid nahi" mark). Yeh `token_blacklist` app (point 5) ke models use karta. Iske bina rotation ka security benefit adhoora  -  purana token abhi bhi chal jaata. **Yahi reason hai `rest_framework_simplejwt.token_blacklist` `INSTALLED_APPS` mein hai.**
- **`USER_ID_CLAIM: "user_id"`**  -  token ke payload mein user ki id `user_id` naam ke claim mein store hoti. Decode karke server jaan leta kaunsa user.

`env.int(...)` se lifetimes configurable hain  -  prod mein chahein toh `.env` se badal sakte, code touch kiye bina.

---

#### 9. `CACHES`  -  Redis vs LocMem, aur prod ka smart fallback

base.py default Redis maanta:

```python
# base.py
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
 "default": {
 "BACKEND": "django.core.cache.backends.redis.RedisCache",
 "LOCATION": REDIS_URL,
 "TIMEOUT": 300,
 }
}
```

Cache = mehenga computation ya DB query ka result temporarily store karna, taaki dobara na karna pade. Redis ek fast in-memory key-value store hai  -  **multiple processes/servers** share kar sakte.

**Dev mein Redis optional:**
```python
# development.py
if not env.bool("DJANGO_DEV_USE_REDIS", default=False):
 CACHES = {"default": {"BACKEND": "...locmem.LocMemCache", "LOCATION": "grindmate-dev"}}
```
**LocMemCache** = process ki RAM mein cache. Koi external server nahi. Dev ko Redis install karne ki zaroorat nahi  -  `clone & run`. Jis din Redis test karna ho, `.env` mein `DJANGO_DEV_USE_REDIS=1`.

**Prod ka clever fallback** (yeh hi portfolio-grade decision hai):
```python
# production.py
if not env("REDIS_URL", default=""):
 CACHES = {"default": {"BACKEND": "...locmem.LocMemCache", "LOCATION": "grindmate-prod"}}
```
**Reasoning:** base.py ka default `redis://localhost:6379/0` hai. Par free-tier deploy (Render) pe Redis na ho toh? Bina is check ke, prod **localhost ke Redis se connect karne ki koshish karega jo exist hi nahi** → har cache call pe `ConnectionError` → 500. Yeh check bolta: "agar prod mein `REDIS_URL` explicitly set nahi hai, toh chup-chaap LocMem use kar lo." **Graceful degradation**  -  caching thodi kamzor (per-process, shared nahi) par app crash nahi karti. Free-tier deploy ke liye perfect.

**Gotcha:** LocMem cache **per-process** hota. Agar gunicorn ke 4 workers hain, har worker ka apna alag cache  -  ek mein set kiya doosre ko nahi dikhega. Isiliye shared/multi-server caching ke liye Redis chahiye. LocMem sirf single-process ya low-traffic ke liye theek.

---

#### 10. Production security headers  -  kya-kya protect karte

`production.py` mein yeh block sirf prod mein active hota (dev mein nahi, warna localhost HTTP toot jaaye):

```python
# production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
```

| Setting | Kya karta / kis attack se bachata |
|---|---|
| `SECURE_SSL_REDIRECT = True` | HTTP request ko HTTPS pe redirect. Plaintext traffic block. |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | Yeh cookies sirf HTTPS pe bheji jaayein. Network sniffing se cookie theft rokta. |
| `SECURE_PROXY_SSL_HEADER` | Render/Railway pe app ke aage ek proxy hota jo HTTPS terminate karke Django ko HTTP forward karta. Yeh header (`X-Forwarded-Proto: https`) Django ko batata "original request actually HTTPS thi." **Iske bina** `SECURE_SSL_REDIRECT` infinite redirect loop bana deta (Django sochta request HTTP hai, redirect karta, proxy phir HTTP bhejta...). |
| `SECURE_HSTS_SECONDS = 1 saal` | HSTS header  -  browser ko bolta "agle 1 saal is domain pe sirf HTTPS use karna, HTTP try mat karna." |
| `HSTS_INCLUDE_SUBDOMAINS` / `HSTS_PRELOAD` | Subdomains pe bhi HSTS; preload se browser ki built-in HSTS list mein aane layak. |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `X-Content-Type-Options: nosniff`  -  browser ko MIME-type guess karne se rokta (MIME confusion attacks). |
| `SECURE_REFERRER_POLICY = "same-origin"` | Referrer header sirf same-origin pe bheja jaaye  -  external sites ko tere internal URLs leak na ho. |
| `X_FRAME_OPTIONS = "DENY"` | Tera site kisi `<iframe>` mein embed na ho  -  **clickjacking** se bachao. |

**HSTS ka gotcha:** Pehli baar deploy pe `SECURE_HSTS_SECONDS` ko chhota (e.g. 60) rakhna behtar, sab sahi confirm hone ke baad badhao. Kyunki HSTS browser mein "cache" ho jaata  -  agar galti se 1-saal set ho gaya aur HTTPS toot gaya, toh users ka browser 1 saal tak HTTP pe gir hi nahi payega.

---

#### 11. `LOGGING`  -  dictConfig anatomy

Django Python ka standard `logging.config.dictConfig` use karta. base.py mein:

```python
LOGGING = {
 "version": 1,
 "disable_existing_loggers": False,
 "formatters": {
 "verbose": {
 "format": "[{asctime}] {levelname} {name} ({funcName}): {message}",
 "style": "{",
 },
 },
 "handlers": {
 "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
 },
 "root": {"handlers": ["console"], "level": "INFO"},
 "loggers": {
 "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
 "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
 "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
 },
}
```

Char concepts:

- **`formatters`**  -  log line kaise dikhe. `verbose` format: `[time] LEVEL logger.name (function): message`. `"style": "{"` matlab `{asctime}` jaise `str.format()` placeholders use ho rahe (Python logging ka default `%`-style hai, yahan `{}`-style chuna  -  readable).
- **`handlers`**  -  log kahan jaaye. `console` = `StreamHandler` = stdout/stderr. **Prod mein file nahi, console kyun?** Kyunki Render/Railway jaise platforms stdout ko khud capture karte (12-factor: "logs as event streams"). File mein likhna ephemeral container mein bekaar  -  restart pe ud jaayega.
- **`root`**  -  fallback logger. Jo bhi log kisi specific logger se match na kare, yahan aata. Level `INFO`.
- **`loggers`**  -  named loggers:
  - `django` `INFO`  -  Django ka internal log (requests, etc.).
  - `celery` `INFO`  -  background tasks.
  - `apps` `DEBUG`  -  **GrindMate ka apna code** (`apps.users`, `apps.leetcode`, etc.). DEBUG level matlab developer ke detailed logs dikhein. Tu code mein `logging.getLogger("apps.leetcode")` se logger banata, yeh us hierarchy se match karta.
- **`propagate: False`**  -  by default ek logger ka message uske parent (aur root) tak bubble up karta. `False` se yeh rukta  -  warna message **do baar** print hota (ek specific logger se, ek root se). Duplicate logs rokta.
- **`disable_existing_loggers: False`**  -  third-party libraries ke pehle se bane loggers ko mat maaro. Default `True` hota jo unhe silent kar deta  -  yahan `False` taaki kuch important na chhoot jaaye.

**Prod overrides** (`production.py`):
```python
LOGGING["loggers"]["apps"]["level"] = "INFO" # DEBUG → INFO
LOGGING["loggers"]["urllib3"] = {... "level": "WARNING" ...}
LOGGING["loggers"]["requests"] = {... "level": "WARNING" ...}
```
- **`apps` ko DEBUG se INFO**  -  prod mein DEBUG logs ka flood nahi chahiye (performance + noise + storage cost). Sirf meaningful INFO+ chahiye.
- **`urllib3` / `requests` ko WARNING**  -  yeh HTTP libraries (LeetCode GraphQL call karte) bahut verbose hain. Har request ka detailed log nahi chahiye prod mein  -  sirf jab kuch galat ho (WARNING+).

Yeh **in-place mutation** pattern (`LOGGING["loggers"]["apps"]["level"] = ...`) chalta hai kyunki `from .base import *` ke baad `LOGGING` dict same object hai  -  usko mutate kar rahe, poora redefine nahi. Clean override.

---

#### Yeh structure "portfolio-grade" kyun hai

1. **Settings split (4-way)**  -  har environment ka behavior alag file mein, explicit. Recruiter/reviewer instantly samajhta tu 12-factor jaanta hai.
2. **Secure by default**  -  DRF `IsAuthenticated` default, prod mein hard `DEBUG=False`, security headers ka full set.
3. **Graceful degradation**  -  Redis na ho toh LocMem fallback (dev aur prod dono). Free-tier deploy crash nahi hota.
4. **Zero-config dev onboarding**  -  SQLite fallback, LocMem cache, console email, eager Celery. Naya banda `clone → migrate → runserver`, bas.
5. **Configurable via env, not code**  -  JWT lifetimes, throttle, sync interval sab `.env` se. Code redeploy ke bina behavior tweak.
6. **Forward-thinking, not over-engineered**  -  ASGI file ready hai par chhoti; named throttle scopes already defined; URL versioning (`/api/v1/`) future migration ke liye.
7. **Production observability**  -  Sentry integration, structured logging, healthcheck endpoint (`/health/`) jo platforms aur CI use karte.

---

#### Interview Questions + Short Answers

1. **Q: `manage.py` mein `setdefault` kyun, plain assignment kyun nahi?**
 A: `setdefault` already-set `DJANGO_SETTINGS_MODULE` ko override nahi karta. Isse CI/test environment apna settings module (e.g. `test`) export karke chala sakta, manage.py usko respect karta  -  sirf tab development thopta jab kuch set na ho.

2. **Q: WSGI aur ASGI mein fark, aur gunicorn `application` kaise uthata?**
 A: WSGI synchronous, ek request = ek blocking call; ASGI async + websockets/long-lived connections support karta. Gunicorn `grindmate.wsgi:application` string se `wsgi` module import karke `application` callable nikaalta, aur har HTTP request pe usse call karta.

3. **Q: `.env` mein value change ki par effect nahi aaya  -  kyun?**
 A: OS environment variable `.env` se priority leta hai. `env.read_env()` already-set OS vars ko overwrite nahi karta, isliye agar shell/CI mein woh var pehle se set ho, woh `.env` ko jeet jaata. Order: OS env > `.env` > code default.

4. **Q: `env.bool("DEBUG", default=False)` ke bajaye `env("DEBUG")` use karein toh kya hoga?**
 A: `env()` string return karta  -  `"False"` ek non-empty string hai jo Python mein truthy hai, toh DEBUG galti se `True` ban jaata (security bug). `env.bool()` `"False"/"0"/"no"` ko sahi `False` mein convert karta.

5. **Q: `BLACKLIST_AFTER_ROTATION=True` ke liye kya extra setup chahiye?**
 A: `rest_framework_simplejwt.token_blacklist` ko `INSTALLED_APPS` mein add karna aur migrate karna  -  yeh blacklist ke DB tables banata. Bina iske rotate hua purana refresh token blacklist nahi ho payega.

6. **Q: MIDDLEWARE mein `SessionMiddleware` ko `AuthenticationMiddleware` ke baad rakh dein toh?**
 A: `AuthenticationMiddleware` `request.session` par depend karta. Session middleware uske baad hoga toh session abhi set nahi hua → `AttributeError`/auth crash. Isliye session pehle, auth baad mein.

7. **Q: Prod mein `REDIS_URL` blank ho toh LocMem fallback kyun, error kyun nahi?**
 A: base.py ka default `redis://localhost` hai jo prod mein exist nahi karta  -  har cache call crash karti. Fallback se app graceful degrade karta (per-process cache), free-tier deploy chalta rehta.

8. **Q: `propagate: False` loggers mein kya rokta?**
 A: Log message ka parent/root logger tak bubble-up hona rokta, jisse same message do baar print hone (duplicate logs) se bachta.

9. **Q: `test.py` `REST_FRAMEWORK = {**REST_FRAMEWORK, ...}` kyun, plain `{...}` kyun nahi?**
 A: Plain redefine se base ki saari DRF config (auth, pagination) gayab ho jaati. `{**REST_FRAMEWORK, ...}` base dict spread karke sirf `DEFAULT_THROTTLE_RATES` override karta, baaki intact.

---

#### Khud Try Kar (Exercises)

1. **Settings resolution trace kar:** `backend/` mein chal  -  `python manage.py shell` aur phir `from django.conf import settings; print(settings.SETTINGS_MODULE, settings.DEBUG, settings.DATABASES["default"]["ENGINE"])`. Ab `$env:DJANGO_SETTINGS_MODULE = "grindmate.settings.production"` set karke (saath mein `DJANGO_SECRET_KEY` aur `DJANGO_ALLOWED_HOSTS` bhi) dobara chala  -  dekh DEBUG aur engine kaise badalte. (Hint: prod `DJANGO_SECRET_KEY` aur `ALLOWED_HOSTS` ke bina crash karega  -  yahi point hai, observe the error.)

2. **OS-env > .env priority khud reproduce kar:** `.env` mein `JWT_ACCESS_TOKEN_LIFETIME_MIN=30` daal. Shell `python -c "from django.conf import settings; ..."` ... actually shell mein `$env:JWT_ACCESS_TOKEN_LIFETIME_MIN = "5"` export kar, phir Django shell mein `settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]` print kar. Confirm woh 5 minutes dikha raha (OS jeeta), 30 nahi. Phir `Remove-Item Env:\JWT_ACCESS_TOKEN_LIFETIME_MIN` karke dobara dekh  -  ab 30 (`.env` jeeta).

3. **Middleware order tod ke seekh:** Ek throwaway branch pe `SessionMiddleware` ko list mein `AuthenticationMiddleware` ke neeche move kar, `runserver` chala aur koi admin page hit kar. Jo error aaye usko padh  -  yeh "order matters" ka concrete proof hai. Phir revert kar de.


---


## 3. Users App  -  Custom User, JWT Auth, Email Verification & Password Reset

Yeh chapter GrindMate ke `apps/users` app pe focused hai. Auth har backend ka dil hota hai aur interview mein sabse zyada yahin se ghuma ghuma ke poocha jaata hai  -  isliye hum yahaan surface scratch nahi karenge. Har cheez ka *kya*, *kyun*, aur *under the hood kaise*  -  teeno khol ke dekhenge, is repo ke actual code se.

Relevant files:
- `backend/apps/users/models.py`
- `backend/apps/users/managers.py`
- `backend/apps/users/serializers.py`
- `backend/apps/users/views.py`
- `backend/apps/users/urls.py`
- `backend/apps/users/signals.py`
- `backend/apps/users/apps.py`
- `backend/grindmate/settings/base.py` (JWT + throttle config)

---

#### 1. Custom User Model  -  `AbstractBaseUser` + `PermissionsMixin`

Django ke saath ek built-in `User` model aata hai (`django.contrib.auth.models.User`). To phir hum apna custom kyun bana rahe hain? Kyunki built-in User mein `username` mandatory hota hai aur login bhi `username` se hota hai. GrindMate mein hum chahte hain ki **login email se ho**, aur username sirf ek public handle ho jo doston ko groups mein dikhe.

Default User ko baad mein badalna **bahut painful** hota hai  -  `AUTH_USER_MODEL` agar pehli migration ke baad change karo to poora DB todna padta hai. Isliye senior devs ka golden rule hai: **din 1 se custom User model rakho**, chahe abhi zaroorat na ho.

`backend/apps/users/models.py`:

```python
class User(AbstractBaseUser, PermissionsMixin):
 id = models.BigAutoField(primary_key=True)
 public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

 email = models.EmailField(_("email address"), unique=True)
 username = models.CharField(
 _("username"), max_length=30, unique=True,
 validators=[USERNAME_REGEX],
 )
 ...
 is_email_verified = models.BooleanField(default=False)
 is_active = models.BooleanField(default=True)
 is_staff = models.BooleanField(default=False)
 ...
 objects = UserManager()

 USERNAME_FIELD = "email"
 REQUIRED_FIELDS = ["username"]
```

##### `AbstractBaseUser` vs `AbstractUser`  -  under the hood

Django do base classes deta hai:

| Class | Kya deta hai | Kab use karein |
|---|---|---|
| `AbstractUser` | Pura ready User (username, first_name, last_name, email, permissions)  -  bas thoda extend karna | Jab tumhe Django ka default schema theek lage |
| `AbstractBaseUser` | Sirf `password`, `last_login`, aur auth ka core machinery (`check_password`, `set_password`, `USERNAME_FIELD`). Baaki sab **tum likho** | Jab tumhe pura control chahiye (email-login jaisa) |

Yahaan `AbstractBaseUser` use hua hai kyunki hum apni field layout chahte the (email-as-login, no first/last name). Iska matlab hum apni `email`, `username`, `is_staff`, `is_active` sab khud declare kar rahe hain.

`PermissionsMixin` alag se add kiya gaya  -  yeh `is_superuser`, `groups`, `user_permissions` fields aur `has_perm()` / `has_module_perms()` methods deta hai. Yeh Django admin aur permission system ke saath compatibility ke liye zaroori hai. `AbstractBaseUser` akela permissions nahi deta  -  isliye dono ko mila ke (`AbstractBaseUser, PermissionsMixin`) inherit kiya gaya hai.

##### `USERNAME_FIELD` aur `REQUIRED_FIELDS`

```python
USERNAME_FIELD = "email"
REQUIRED_FIELDS = ["username"]
```

- `USERNAME_FIELD = "email"`  -  yeh Django ko batata hai ki "login identifier email hai, username nahi". Iske base pe `authenticate()`, admin login, aur SimpleJWT sab email se kaam karte hain. Yeh field automatically `unique=True` honi chahiye (humne kiya hai).
- `REQUIRED_FIELDS`  -  yeh **sirf `createsuperuser` command** ke liye matter karta hai. Iska matlab: "jab CLI se superuser banao, to email aur password ke alawa `username` bhi maango." Important gotcha: `USERNAME_FIELD` aur `password` ko `REQUIRED_FIELDS` mein **kabhi nahi** daalte  -  woh implicitly required hote hain, aur double daalne pe Django error deta hai.

##### `public_id` UUID  -  internal PK leak na ho

```python
id = models.BigAutoField(primary_key=True)
public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
```

Yeh ek **bahut achha security/design decision** hai. Do alag IDs hain:

- `id`  -  auto-increment integer PK (`1, 2, 3...`). Yeh internal use ke liye  -  FKs, joins, fast indexing. Integer PK ORM ke liye sabse efficient hota hai.
- `public_id`  -  random UUID jo API responses mein bahar jaata hai (dekho `UserSerializer` mein `public_id` hai, `id` nahi).

**Kyun?** Agar tum API mein integer `id` expose karo, to attacker `/api/users/1/`, `/api/users/2/` ghuma ke andaaza laga sakta hai ki tumhare paas kitne users hain (enumeration), aur sequential IDs se business intelligence leak hoti hai (e.g. "yeh banda user #5 hai, matlab early adopter"). UUID random hai  -  guess nahi kar sakte. Isko **IDOR (Insecure Direct Object Reference)** protection bhi kehte hain.

`editable=False` ka matlab  -  yeh field forms/admin mein edit nahi ho sakti. `default=uuid.uuid4`  -  yahaan `uuid4` ko **call nahi kiya** (`uuid4()` nahi likha), sirf function pass kiya hai. Django har naye row pe is function ko khud call karega, taaki har user ka apna unique UUID bane. Agar `uuid.uuid4()` likh dete to woh ek hi baar evaluate hota (class load time pe) aur sab users ko same UUID milta  -  classic gotcha.

##### Indexes aur Meta

```python
class Meta:
 ordering = ("-date_joined",)
 indexes = [
 models.Index(fields=["username"]),
 models.Index(fields=["email"]),
 ]
```

`email` aur `username` already `unique=True` hain  -  aur `unique=True` apne aap ek unique index banata hai DB mein. To phir explicit `Index` kyun? Kuch databases pe unique constraint aur lookup index ka behaviour thoda alag hota hai, aur in fields pe hum **bahut frequently filter** karte hain (`email__iexact=email` har login/reset pe). Explicit index intent clear karta hai aur lookups ko fast rakhta hai  -  index hone se DB ko poora table scan nahi karna padta, woh seedha B-tree mein jump kar leta hai.

`ordering = ("-date_joined",)`  -  default ordering newest-first. Gotcha: yeh har query pe `ORDER BY` lagata hai jab tak tum explicitly `.order_by()` na karo, jo kabhi-kabhi unnecessary cost hota hai.

`__str__` aur `name` property bas readability ke liye hain:
```python
def __str__(self) -> str:
 return self.username or self.email

@property
def name(self) -> str:
 return self.display_name or self.username
```
`name` property emails mein use hoti hai (`Hi {user.name}`)  -  agar display_name set hai to woh, warna username.

---

#### 2. Custom `UserManager`  -  model ka "table-level" interface

Pehle samajh: **Manager kya hota hai?** Har Django model pe ek `objects` attribute hota hai  -  `User.objects.all()`, `User.objects.filter(...)`. Yeh `objects` ek **Manager** instance hai. Manager woh gateway hai jisse tum **table-level operations** karte ho (poore table pe queries). Ek single row pe jo methods chalte hain (jaise `user.set_password()`) woh model pe hote hain; poore table ke operations (`create`, `filter`, `all`) Manager pe.

`backend/apps/users/managers.py`:

```python
class UserManager(BaseUserManager):
 use_in_migrations = True

 def _create_user(self, email, password, **extra_fields):
 if not email:
 raise ValueError("Users must have an email address.")
 if not extra_fields.get("username"):
 raise ValueError("Users must have a username.")
 email = self.normalize_email(email)
 user = self.model(email=email, **extra_fields)
 user.set_password(password)
 user.save(using=self._db)
 return user

 def create_user(self, email, password=None, **extra_fields):
 extra_fields.setdefault("is_staff", False)
 extra_fields.setdefault("is_superuser", False)
 return self._create_user(email, password, **extra_fields)

 def create_superuser(self, email, password=None, **extra_fields):
 extra_fields.setdefault("is_staff", True)
 extra_fields.setdefault("is_superuser", True)
 extra_fields.setdefault("is_email_verified", True)
 if extra_fields.get("is_staff") is not True:
 raise ValueError("Superuser must have is_staff=True.")
 if extra_fields.get("is_superuser") is not True:
 raise ValueError("Superuser must have is_superuser=True.")
 return self._create_user(email, password, **extra_fields)
```

##### Kyun custom Manager chahiye?

Jab tum `USERNAME_FIELD = "email"` karte ho, to Django ka default `UserManager` toot jaata hai  -  kyunki uska `create_user(username, email, password)` signature username-based hai. SimpleJWT, `createsuperuser`, tests  -  sab `User.objects.create_user(...)` / `create_superuser(...)` call karte hain. Inhe email-first banane ke liye humein apna Manager likhna padta hai.

##### Teen-layer pattern: `_create_user` → `create_user` → `create_superuser`

Yeh classic DRY pattern hai:
- `_create_user` (underscore = "private/internal")  -  actual kaam: validation + normalize + hash + save. Ek hi jagah.
- `create_user`  -  normal user defaults (`is_staff=False`, `is_superuser=False`) set karke `_create_user` call.
- `create_superuser`  -  admin defaults set karke `_create_user` call. Saath mein **defensive checks**  -  agar koi galti se `is_superuser=False` pass kare to error, taaki "superuser jo actually superuser nahi" jaisa inconsistent state na bane. Notice: superuser ka `is_email_verified=True` automatically set hota hai  -  admin ko email verify karne ki zaroorat nahi.

##### `normalize_email`  -  kya karta hai

`self.normalize_email(email)` `BaseUserManager` se aata hai. Yeh email ke **domain part ko lowercase** kar deta hai (`Foo@GMAIL.COM` → `Foo@gmail.com`). Note: local part (@ se pehle) ko touch nahi karta kyunki technically woh case-sensitive ho sakta hai. Yeh duplicate signups (Gmail.com vs gmail.com) ko kam karta hai. Isiliye login/lookup mein `email__iexact` use hota hai  -  taaki case-insensitive match ho.

##### `set_password`  -  yahaan password hash hota hai (next section mein deep)

```python
user.set_password(password)
```
Yeh **kabhi plain password store nahi karta**  -  hash karke `password` field mein daalta hai. Yeh line poore auth system ki sabse important line hai. Detail Section 3 mein.

##### `use_in_migrations = True`

```python
use_in_migrations = True
```

Yeh batata hai ki yeh Manager **migrations mein serialize ho sakta hai**. Jab tum data migration likhte ho jo `User.objects.create_user(...)` use karna chahti hai (historical model pe), to Django ko Manager ko reconstruct karna padta hai. `use_in_migrations = True` iski permission deta hai. **Catch:** iske liye Manager ke `__init__` mein koi positional args nahi hone chahiye  -  yahaan default `__init__` hai to safe hai.

`self.model` = woh model class jisse Manager attached hai (`User`). `self._db` = current database alias (multi-DB setups ke liye, default `"default"`). `self.model(...)` se ek unsaved instance banta hai, phir password set karke `save()` hota hai.

---

#### 3. Password Hashing  -  `pbkdf2_sha256`, salt, iterations (User ne yeh specifically poocha tha)

Yeh interview ka **hottest** topic hai. Dhyan se.

##### Plain password kabhi store nahi hota

Agar DB leak ho jaaye (hota rehta hai), aur tumne plain passwords store kiye, to har user ka password attacker ke paas. Aur log passwords reuse karte hain  -  to tumhare leak se unka bank account bhi gaya. Isliye hum password ko **one-way hash** karke store karte hain. One-way matlab: hash se wapas original password nikalna computationally impossible (practically).

##### `set_password` vs `check_password`

```python
# Likhte waqt (manager._create_user):
user.set_password(password) # plain -> hash, model ke .password field mein daal deta hai

# Verify karte waqt (ChangePasswordSerializer):
user.check_password(value) # plain ko hash karke stored hash se compare; True/False
```

`set_password` plain password leta hai, hash banata hai, aur `self.password` mein store karta hai (DB save tumhe alag se karna padta hai). `check_password` plain password leta hai, **usi salt + algo** se dobara hash banata hai, aur stored hash se compare karta hai. Important: yeh `==` se compare nahi karta  -  **constant-time comparison** karta hai taaki timing attack na ho (jismein attacker response time se andaaza lagaye ki kitne characters match hue).

##### Stored hash ka format  -  under the hood

Django password field mein aisa kuch store hota hai (4 parts, `$` se separated):

```
pbkdf2_sha256$1000000$kQp2Xr...salt...$base64encodedhash=
└------┬-----┘ └--┬--┘ └-----┬------┘ └--------┬--------┘
 algorithm iterations salt actual hash
```

- **algorithm**  -  `pbkdf2_sha256` (Django ka default). PBKDF2 = Password-Based Key Derivation Function 2, andar SHA-256 use karta hai.
- **iterations**  -  hash function ko itni baar repeat karo (Django mein lakhs mein, version pe depend). Yeh deliberately **slow** banata hai  -  taaki attacker brute-force kare to har guess mehnga pade. (Slow-for-passwords intentional design hai.)
- **salt**  -  har user ke liye ek **random unique string** jo password ke saath mila ke hash banta hai. Yeh "rainbow table" attack rokta hai  -  pre-computed hash tables bekaar ho jaate hain kyunki salt har baar alag. Do users ka same password ho phir bhi hash alag, kyunki salt alag.
- **hash**  -  final output.

##### Kaun decide karta hai konsa algo?

`PASSWORD_HASHERS` setting (humne base.py mein override nahi kiya, to Django ka default chalta hai  -  pehla `PBKDF2PasswordHasher`). Interesting: `backend/grindmate/settings/test.py:14` mein:

```python
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
```

**Tests mein MD5 deliberately use hota hai** kyunki MD5 fast hai  -  pbkdf2 ke lakhs iterations test suite ko slow kar dete (har `UserFactory` user banane pe hashing). MD5 production mein **kabhi nahi**  -  sirf tests mein speed ke liye. Yeh ek smart trade-off hai jo CLAUDE.md style portfolio projects mein common hai.

##### Password validators

`backend/grindmate/settings/base.py:110`:
```python
AUTH_PASSWORD_VALIDATORS = [
 {"NAME": "...UserAttributeSimilarityValidator"},
 {"NAME": "...MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
 {"NAME": "...CommonPasswordValidator"},
 {"NAME": "...NumericPasswordValidator"},
]
```
Yeh **hashing se pehle** chalte hain  -  weak passwords reject karne ke liye. Serializers mein `validators=[validate_password]` (dekho `RegisterSerializer.password`) inhi validators ko trigger karta hai. Validation order: pehle DRF field validation → `validate_password` → tab manager `set_password` → tab hash.

##### Gotcha: kabhi `user.password = "abc"` mat karo

```python
user.password = "mypass123" # GALAT  -  yeh plain text DB mein daal dega!
user.set_password("mypass123") # SAHI  -  hash karta hai
```
Agar tum directly `.password` assign karoge, woh raw string store hoga aur `check_password` kabhi match nahi karega (kyunki woh hash format expect karta hai). Hamesha `set_password`.

---

#### 4. JWT  -  Deep Dive (sabse important section)

Yeh chapter ka core hai. Ek-ek cheez khol ke.

##### JWT hota kya hai?

JWT = **JSON Web Token**. Yeh ek **string** hai jo teen parts mein bata hua hai, `.` (dot) se:

```
eyJhbGciOiJIUzI1NiJ9 . eyJ1c2VyX2lkIjo0Mn0 . dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1
└------ HEADER ------┘  └----- PAYLOAD -----┘  └------------ SIGNATURE ----------┘
 (base64url JSON) (base64url JSON) (HMAC SHA-256 of header.payload)
```

1. **Header**  -  JSON jismein algo bataya jaata hai: `{"alg": "HS256", "typ": "JWT"}`. base64url-encode hota hai.
2. **Payload (claims)**  -  actual data: `{"user_id": 42, "exp": 1716998400, "username": "anveet", ...}`. base64url-encode hota hai. **Yahaan dhyan do  -  yeh sirf encode hai, encrypt nahi.** Koi bhi banda payload ko decode karke padh sakta hai (jaao [jwt.io](https://jwt.io) pe paste karke dekho). Isliye payload mein **secret data kabhi mat daalo**  -  password, credit card, kuch nahi.
3. **Signature**  -  server `header.payload` ko apni **secret key** (Django ka `SECRET_KEY`) se HMAC-SHA256 karke signature banata hai. Yeh **tamper-proofing** deta hai: agar koi payload badle (e.g. `user_id` 42 se 1 kar de admin banne ke liye), to signature match nahi karega kyunki secret sirf server ke paas hai. Server verify karega aur reject kar dega.

**Key insight:** JWT confidentiality nahi, **integrity** deta hai. Koi padh sakta hai, par bina secret ke badal nahi sakta.

##### Stateless auth  -  yeh JWT ka asli faayda

Traditional session auth: server DB/cache mein session store karta hai, browser ko ek session-id cookie deta hai. Har request pe server DB se session lookup karta hai. **Stateful**  -  server ko sab sessions yaad rakhne padte hain.

JWT **stateless** hai: token mein hi `user_id` aur expiry hai, server ki **secret se signed**. Server ko kuch yaad rakhne ki zaroorat nahi  -  har request pe woh sirf signature verify karta hai aur payload se `user_id` nikaal leta hai. Isse:
- Server side koi session storage nahi (scale karna aasaan  -  koi bhi server instance request handle kar sakta hai).
- DB lookup bachta hai (signature verification pure CPU hai, fast).

GrindMate free-tier pe deploy hota hai (MEMORY.md), jahan Redis-backed session store costly/limited hai. Stateless JWT yahaan perfect fit hai.

##### Access vs Refresh token  -  do tokens kyun?

Stateless ka ek problem hai: **token revoke karna mushkil**. Agar token chori ho gaya, to expiry tak valid rahega  -  server "yaad" nahi rakhta. Solution: do tokens.

| Token | Lifetime (is repo) | Kaam |
|---|---|---|
| **Access token** | 15 min (`JWT_ACCESS_TOKEN_LIFETIME_MIN`, default 15) | Har API request ke saath jaata hai. Short-lived, taaki chori ho to jaldi bekaar ho. |
| **Refresh token** | 7 days (`JWT_REFRESH_TOKEN_LIFETIME_DAYS`, default 7) | Sirf naya access token lene ke liye. Long-lived, par sirf ek endpoint pe use hota hai. |

`backend/grindmate/settings/base.py:159`:
```python
SIMPLE_JWT = {
 "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MIN", default=15)),
 "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
 "ROTATE_REFRESH_TOKENS": True,
 "BLACKLIST_AFTER_ROTATION": True,
 "AUTH_HEADER_TYPES": ("Bearer",),
 "USER_ID_FIELD": "id",
 "USER_ID_CLAIM": "user_id",
}
```

Logic: user 15 min access token use karta rahta hai. Expire hone pe, frontend chupke se refresh token bhej ke naya access token le leta hai  -  user ko dobara login nahi karna padta. 7 din tak yeh chalta hai; phir refresh bhi expire, dobara login.

- `AUTH_HEADER_TYPES: ("Bearer",)`  -  header `Authorization: Bearer <token>` format mein expect hota hai.
- `USER_ID_FIELD: "id"` / `USER_ID_CLAIM: "user_id"`  -  token ke andar `id` field (humara integer PK) ko `user_id` claim ke naam se store karo. Verification ke waqt SimpleJWT `user_id` se `User.objects.get(id=...)` karke request.user set karta hai.

##### Har request mein Bearer token kaise jaata hai

Frontend access token ko `Authorization` header mein bhejta hai:
```
GET /api/v1/auth/me/ HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo0Mn0.dBjftJ...
```

Server side, `base.py:136`:
```python
"DEFAULT_AUTHENTICATION_CLASSES": (
 "rest_framework_simplejwt.authentication.JWTAuthentication",
 "rest_framework.authentication.SessionAuthentication",
),
```
`JWTAuthentication` har request pe yeh karta hai:
1. `Authorization` header padhta hai, `Bearer ` ke baad ka token nikaalta hai.
2. Signature verify karta hai (`SECRET_KEY` se). Galat ho to 401.
3. `exp` claim check karta hai  -  expired to 401.
4. `user_id` claim se `User.objects.get(id=user_id)`  -  `request.user` set ho jaata hai.

Iske baad views mein `permission_classes = (IsAuthenticated,)` `request.user` check kar leta hai. (`SessionAuthentication` browsable API/admin ke liye fallback hai.)

##### Pura token flow (ASCII)

```
┌----------┐ ┌----------┐
│ FRONTEND │ │  SERVER  │
└----┬-----┘ └----┬-----┘
 │ │
 │ 1) POST /auth/login/  {email, password} │
 │-------------------------------------------------------->
 │ GrindMateTokenObtainPairSerializer:
 │ - authenticate(email, password)
 │ - is_email_verified gate
 │ - get_token() -> sign access+refresh
 │ {access, refresh, user} │
 <--------------------------------------------------------│
 │  (store access in memory, refresh in httpOnly/secure) │
 │ │
 │ 2) GET /auth/me/ Authorization: Bearer <access> │
 │-------------------------------------------------------->
 │ JWTAuthentication:
 │ - verify signature + exp
 │ - user_id claim -> request.user
 │ 200 {user profile} │
 <--------------------------------------------------------│
 │ │
 │ ... 15 min baad access expire ... │
 │ │
 │ 3) GET /auth/me/ Authorization: Bearer <expired> │
 │-------------------------------------------------------->
 │ 401 token_not_valid │
 <--------------------------------------------------------│
 │ │
 │ 4) POST /auth/token/refresh/  {refresh} │
 │-------------------------------------------------------->
 │ TokenRefreshView:
 │ - verify refresh signature+exp
 │ - ROTATE: issue NEW refresh
 │ - BLACKLIST old refresh
 │ {access: <new>, refresh: <new>} │
 <--------------------------------------------------------│
 │  (retry the original request with new access) │
 │ │
 │ 5) POST /auth/logout/  {refresh} │
 │-------------------------------------------------------->
 │ LogoutView:
 │ RefreshToken(refresh).blacklist()
 │ 205 Reset Content │
 <--------------------------------------------------------│
```

##### `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` + blacklist app

Yeh do settings stateless JWT ki security badi badha dete hain.

- `ROTATE_REFRESH_TOKENS = True`  -  har baar jab refresh token use karke naya access maangte ho, server ek **naya refresh token bhi** deta hai. Purana ab use nahi hoga.
- `BLACKLIST_AFTER_ROTATION = True`  -  purane refresh token ko **blacklist** kar deta hai (DB mein "yeh token ab invalid hai" mark). Agar attacker ne purana refresh chura liya tha aur use kare, to woh blacklisted milega → reject.

Yeh **token rotation** detection deta hai: agar ek refresh token do baar use ho (legit user + attacker dono), to second use blacklisted token hit karega aur pakda jaayega.

Iske liye `base.py:42` mein app install hai:
```python
"rest_framework_simplejwt.token_blacklist",
```
Yeh do tables banata hai: `OutstandingToken` (saare issued refresh tokens) aur `BlacklistedToken`. **Note ka point:** blacklist ek **chhota stateful exception** hai pure stateless model mein  -  sirf refresh tokens track hote hain (jo 7 din baad waise bhi expire). Access tokens (jo har request pe aate hain) abhi bhi pure stateless verify hote hain, koi DB hit nahi. Yeh ek smart balance hai: performance (access tokens stateless) + revocation power (refresh tokens trackable).

##### Logout  -  blacklist in action

`backend/apps/users/views.py:49`:
```python
class LogoutView(APIView):
 permission_classes = (permissions.IsAuthenticated,)
 def post(self, request, *_args, **_kwargs):
 refresh = request.data.get("refresh")
 if not refresh:
 return Response({"detail": "Refresh token required."}, status=400)
 try:
 RefreshToken(refresh).blacklist()
 except Exception:
 return Response({"detail": "Invalid or expired token."}, status=400)
 return Response(status=status.HTTP_205_RESET_CONTENT)
```
Stateless JWT mein "logout" matlab kya? Access token to khud 15 min mein expire ho jaayega  -  usko revoke nahi kar sakte (woh stateless hai). Par refresh token ko **blacklist** kar sakte hain, taaki logout ke baad naya access na liya ja sake. `205 Reset Content` ek thoda unusual par semantically valid status hai  -  "tumhara state reset karo (tokens phenk do)".

##### `GrindMateTokenObtainPairSerializer`  -  login ka custom magic

`backend/apps/users/serializers.py:56`:
```python
class GrindMateTokenObtainPairSerializer(TokenObtainPairSerializer):
 @classmethod
 def get_token(cls, user):
 token = super().get_token(user)
 token["username"] = user.username
 return token

 def validate(self, attrs):
 data = super().validate(attrs)
 if not self.user.is_email_verified:
 raise exceptions.AuthenticationFailed(
 "Email not verified. Check your inbox for the verification link "
 "or request a new one.",
 code="email_not_verified",
 )
 data["user"] = UserSerializer(self.user).data
 return data
```

Yahaan SimpleJWT ke default serializer ko extend karke **teen** cheezein kiye hain:

1. **`get_token` override  -  custom claim.** `super().get_token(user)` standard refresh token banata hai (`user_id`, `exp`, etc.). Hum usmein `token["username"] = user.username` add karte hain. Ab username dono tokens ke payload mein chala jaata hai  -  frontend access token decode karke `username` dikha sakta hai bina API call ke. Yaad rahe: payload publicly readable hai, isliye `username` (public handle) daalna fine hai, par kabhi sensitive cheez nahi.

2. **`validate` override  -  email-verified gate.** `super().validate(attrs)` credentials check karke tokens generate karta hai aur `self.user` set karta hai. Uske **baad** hum check karte hain  -  agar email verify nahi hua, to `AuthenticationFailed` raise. Matlab: galat password = fail, **aur** sahi password par unverified email = bhi fail. Custom `code="email_not_verified"` frontend ko exact reason batata hai taaki woh "resend verification" button dikha sake. Yeh login ka business-rule gate hai jo serializer level pe enforce hota hai.

3. **User payload embed  -  extra `/me` round-trip bachaata.** `data["user"] = UserSerializer(self.user).data`. Normally login ke baad frontend ko user profile ke liye `/me` alag se call karna padta. Yahaan hum login response mein hi user object thoonk dete hain. Ek network round-trip bach gaya  -  login snappy lagta hai. Yeh ek chhota par solid UX/performance decision hai.

Yeh serializer `LoginView` mein wire hota hai (`views.py:42`):
```python
class LoginView(TokenObtainPairView):
 serializer_class = GrindMateTokenObtainPairSerializer
 permission_classes = (permissions.AllowAny,)
```
Aur refresh ke liye `urls.py:14` mein SimpleJWT ka stock view use hua hai:
```python
path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
```

###### JWT gotchas (interview gold)

- **Payload encrypted nahi hai**  -  base64 hai. Decode karke koi bhi padh sakta hai. Secret kabhi mat daalo.
- **`alg: none` attack**  -  purane JWT libs mein agar header `"alg": "none"` ho to signature skip ho jaata tha. SimpleJWT isse safe hai (algo server-fixed hai), par concept yaad rakho.
- **Logout truly instant nahi**  -  access token blacklist nahi hota, to logout ke baad bhi woh access token uski expiry (max 15 min) tak valid rehta hai. Trade-off hai stateless ka.
- **Clock skew**  -  `exp` server time pe based hai. Agar servers ka time off ho to tokens jaldi/der se expire ho sakte. SimpleJWT mein leeway config hota hai.

---

#### 5. DRF Serializers  -  validation + (de)serialization layer

Serializer ka kaam do-tarfa hai:
- **Serialization**  -  Python/Django object → JSON (response ke liye). `UserSerializer(user).data` → dict.
- **Deserialization + validation**  -  incoming JSON → validate → Python dict / model instance. `serializer.is_valid()`.

Soch isko ek **gatekeeper + translator** ki tarah: bahar jaata data clean karta hai, andar aata data check karta hai.

##### `ModelSerializer`  -  model se auto fields

`UserSerializer` (`serializers.py:13`):
```python
class UserSerializer(serializers.ModelSerializer):
 class Meta:
 model = User
 fields = ("public_id", "username", "email", "display_name",
 "avatar_url", "timezone", "is_email_verified", "date_joined")
 read_only_fields = ("public_id", "is_email_verified", "date_joined")
```
`ModelSerializer` model ko dekh ke automatically fields infer kar leta hai (type, validators). `fields` explicitly list karte hain  -  **`id` aur `password` yahaan nahi hain**. Yeh deliberate: `id` (internal PK) bahar nahi jaata, sirf `public_id`. Aur `password` to kabhi expose nahi.

`read_only_fields`  -  yeh fields response mein aati hain par PATCH/PUT se badli nahi ja saktin. `is_email_verified` ko user khud true nahi kar sakta (warna verification bekaar), `public_id`/`date_joined` system-generated hain.

##### `write_only` fields  -  `RegisterSerializer`

`serializers.py:31`:
```python
class RegisterSerializer(serializers.ModelSerializer):
 password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
 password_confirm = serializers.CharField(write_only=True, required=True)

 class Meta:
 model = User
 fields = ("email", "username", "display_name", "password", "password_confirm")

 def validate(self, attrs):
 if attrs["password"] != attrs["password_confirm"]:
 raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
 return attrs

 def create(self, validated_data):
 validated_data.pop("password_confirm")
 password = validated_data.pop("password")
 return User.objects.create_user(password=password, **validated_data)
```

- `write_only=True`  -  yeh field input mein accept hoti hai par **output mein kabhi nahi** jaati. Password input mein aata hai, par response mein password kabhi echo nahi hota. Critical security feature.
- `validators=[validate_password]`  -  register pe woh `AUTH_PASSWORD_VALIDATORS` chalte hain (min length, common-password, etc.).
- `password_confirm` model field nahi hai  -  sirf serializer-level field. Isliye `create` mein `.pop()` karke nikaal dete hain, warna `create_user(**validated_data)` ko unexpected kwarg milta.

##### `validate()` vs `validate_<field>()`

Yeh **bahut poocha jaata** hai interview mein:

| Method | Scope | Kab |
|---|---|---|
| `validate_<field>(self, value)` | Single field | Ek field ki standalone validation. e.g. `ChangePasswordSerializer.validate_old_password` |
| `validate(self, attrs)` | Pura object (cross-field) | Jab do/zyada fields ek doosre pe depend karein. e.g. password == password_confirm |

`RegisterSerializer.validate` cross-field hai  -  password aur password_confirm dono chahiye compare karne ke liye, isliye object-level `validate`. Yeh field-level validators ke **baad** chalta hai (DRF pehle har field validate karta hai, phir object-level).

`ChangePasswordSerializer` (`serializers.py:78`) field-level dikhata hai:
```python
class ChangePasswordSerializer(serializers.Serializer):
 old_password = serializers.CharField(required=True)
 new_password = serializers.CharField(required=True, validators=[validate_password])

 def validate_old_password(self, value):
 user = self.context["request"].user
 if not user.check_password(value):
 raise serializers.ValidationError("Current password is incorrect.")
 return value
```
Notice `self.context["request"]`  -  view serializer ko `context={"request": request}` pass karta hai (`views.py:87`), taaki serializer ke paas current user ho `check_password` ke liye. Yeh `Serializer` hai (`ModelSerializer` nahi) kyunki yeh koi model create/update nahi karti  -  bas validate karke view password set karta hai.

##### `create()` flow  -  register ka full path

`create()` tab call hota hai jab `serializer.save()` chale (jo `CreateAPIView` automatically karta hai). Flow:
1. `validated_data` se `password_confirm` pop (model field nahi).
2. `password` pop (alag se manager ko pass karna hai).
3. `User.objects.create_user(password=password, **validated_data)`  -  yahaan manager ka custom logic chalta hai: validation → normalize_email → **set_password (hash)** → save.

Critical: register **kabhi** `User(**data).save()` nahi karta  -  woh password hash nahi karta. `create_user` se hi jaata hai, taaki hashing guarantee ho.

Baaki serializers (`EmailVerifySerializer`, `ResendVerificationSerializer`, `PasswordResetRequestSerializer`, `PasswordResetConfirmSerializer`) plain `Serializer` hain  -  sirf input shape validate karte hain (token string hai? email valid hai?), koi model bind nahi.

---

#### 6. `APIView` vs Generics  -  kab kya

DRF do style deta hai views likhne ke:

| Style | Kya | Kab use karein |
|---|---|---|
| `APIView` | Lowest level  -  tum `get`/`post` khud likhte ho, full control | Jab logic standard CRUD se hatke ho |
| Generics (`CreateAPIView`, `RetrieveUpdateAPIView`, ...) | Pre-built CRUD  -  bas `serializer_class` + `queryset`/`get_object` do | Jab standard create/read/update/delete ho |

GrindMate dono smartly use karta hai:

**Generics jahan standard hai:**
```python
class RegisterView(generics.CreateAPIView): # POST -> create
 serializer_class = RegisterSerializer
 permission_classes = (permissions.AllowAny,)
 throttle_classes = (ScopedRateThrottle,)
 throttle_scope = "register"

class MeView(generics.RetrieveUpdateAPIView):  # GET + PATCH/PUT
 serializer_class = UserSerializer
 permission_classes = (permissions.IsAuthenticated,)
 def get_object(self):
 return self.request.user
```

- `CreateAPIView`  -  `post()` khud handle karta hai: serializer instantiate, validate, `save()` (jo `create()` call karta hai), 201 return. Hum sirf serializer aur permissions dete hain. Boilerplate zero.
- `RetrieveUpdateAPIView`  -  `get()` (retrieve) + `put()`/`patch()` (update) deta hai. Normally yeh URL se `pk` leke object dhoondta hai (`get_object` default `queryset.get(pk=...)`). Par humein **current logged-in user** chahiye, koi arbitrary user nahi. Isliye `get_object` override:
  ```python
  def get_object(self):
 return self.request.user
  ```
  Yeh `/me/` ko "tumhara apna profile" bana deta hai  -  URL mein koi ID nahi, JWT se user aata hai. Security bonus: user kisi aur ka profile fetch/edit nahi kar sakta, kyunki `get_object` hamesha `request.user` deta hai.

**`APIView` jahan logic custom hai:** `LogoutView`, `ChangePasswordView`, `VerifyEmailView`, `ResendVerificationView`, `PasswordResetRequestView/ConfirmView`  -  yeh sab `APIView` hain kyunki inka logic standard CRUD nahi (token consume karna, blacklist karna, email bhejna). Yahaan generics fit nahi baithta, to `post()` khud likha gaya.

`LoginView` (`TokenObtainPairView`) aur `TokenRefreshView` SimpleJWT ke ready-made `APIView` subclasses hain.

---

#### 7. `EmailVerificationToken` & `PasswordResetToken`  -  single-use token pattern

Dono models structurally identical hain, sirf expiry alag. Yeh ek **single-use, time-bound token** pattern hai  -  har secure "email-link" flow ka base.

`models.py:122` (verification) aur `models.py:153` (reset):
```python
class EmailVerificationToken(models.Model):
 EXPIRY = timedelta(hours=24)
 user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_verification_tokens")
 token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
 created_at = models.DateTimeField(auto_now_add=True)
 used_at = models.DateTimeField(null=True, blank=True)

 class Meta:
 indexes = [models.Index(fields=["token"])]

 def is_expired(self) -> bool:
 return django_tz.now() > self.created_at + self.EXPIRY

 def is_usable(self) -> bool:
 return self.used_at is None and not self.is_expired()

 def consume(self) -> None:
 self.used_at = django_tz.now()
 self.save(update_fields=["used_at"])
```

##### `secrets.token_urlsafe`  -  kyun yeh, not `random`

```python
token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
```
`secrets` module **cryptographically secure** random deta hai  -  `random` module nahi (woh predictable hai, seed se reproduce ho sakta hai). Auth tokens guess-proof hone chahiye, isliye `secrets`. `token_urlsafe` URL-safe base64 string deta hai (default ~43 chars, ~256 bits entropy)  -  directly URL mein daal sakte ho bina encoding ke. Phir se: `default=secrets.token_urlsafe` (function pass kiya, call nahi)  -  har row ko fresh token milta hai.

##### Single-use logic  -  `is_usable` + `consume`

- `used_at` null = abhi tak use nahi hua. `consume()` ise `now()` set kar deta hai → token "khatam".
- `is_usable()` = `used_at is None AND not expired`. Dono check ek jagah encapsulate  -  view sirf `if not token.is_usable()` likhta hai, logic model mein. Yeh **fat models, thin views** principle hai  -  business rules model pe.
- `update_fields=["used_at"]`  -  `save()` ko sirf yeh ek column update karne ko bolta hai, poora row nahi. Faster + safer (race conditions kam).

##### 24h vs 1h expiry  -  design reasoning

Code ke docstrings hi reason bata dete hain:
```python
class EmailVerificationToken: # EXPIRY = 24h
class PasswordResetToken: # EXPIRY = 1h  -  "shorter than verify
 # because it lets an attacker change the password"
```
- **Verification 24h**  -  kam risk. Worst case agar leak ho, attacker bas email "verified" kar dega. User ko time chahiye email kholne ka, isliye comfortable 24h.
- **Reset 1h**  -  **high risk**. Yeh token password badal sakta hai = full account takeover. Isliye attack window minimize  -  1 ghanta. Yeh ek classic **risk-based expiry** decision hai jo interview mein bolna chahiye.

`on_delete=models.CASCADE`  -  user delete hua to uske tokens bhi gaye. Token user ke bina meaningless hai, isliye cascade theek.

---

#### 8. Full Flows  -  step by step

##### A) Register → verify → login gate

```
1. POST /api/v1/auth/register/ {email, username, display_name, password, password_confirm}
 └- RegisterView (CreateAPIView)
 └- RegisterSerializer.validate()  -> passwords match?
 └- .create() -> User.objects.create_user()  -> password HASHED, user saved
 (is_email_verified = False default)
 └- post_save signal fires (created=True, not verified):
 └- EmailVerificationToken.objects.create(user) # secrets token
 └- send_mail(verify_link) # FRONTEND_URL/verify-email?token=...
 └- 201 Created

2. User email kholta hai, link click -> frontend /verify-email page -> 
 POST /api/v1/auth/verify-email/ {token}
 └- VerifyEmailView
 └- EmailVerificationToken.objects.select_related("user").get(token=...)
 (not found -> 400 "Invalid token")
 └- if not token.is_usable() -> 400 "Token expired or already used"
 └- token.consume() # single-use mark
 └- user.is_email_verified = True; save(update_fields=["is_email_verified"])
 └- 200 "Email verified."

3. POST /api/v1/auth/login/ {email, password}
 └- LoginView -> GrindMateTokenObtainPairSerializer.validate()
 └- super().validate() -> credentials check (check_password under hood)
 └- if not user.is_email_verified -> AuthenticationFailed("email_not_verified")  # GATE
 └- data["user"] = UserSerializer(user).data
 └- 200 {access, refresh, user}
```

Notice `select_related("user")` in `VerifyEmailView` (`views.py:104`)  -  yeh ek **single SQL JOIN** mein token + uska user dono le aata hai. Bina iske, `token.user` access karne pe ek extra query lagti (N+1 ka chhota version). Hum aage `token.user.is_email_verified = ...` use karte hain, isliye eager-load karna efficient.

##### B) Resend verification (`views.py:125`)

```
POST /api/v1/auth/resend-verification/ {email}
 └- user = User.objects.filter(email__iexact=email, is_email_verified=False).first()
 └- if user is not None:
 new token + send_mail (try/except  -  failure logged, not raised)
 └- ALWAYS 202 Accepted  "If that email belongs to an unverified account, a new link is on the way."
```
Chahe email exist kare ya na kare, verified ho ya na ho  -  **hamesha same 202 + same message**. Yeh enumeration-safe hai (neeche).

##### C) Password reset (`views.py:166`, `views.py:207`)

```
1. POST /api/v1/auth/password-reset/request/ {email}
 └- user = User.objects.filter(email__iexact=email, is_active=True).first()
 └- if user: PasswordResetToken.create + send_mail(reset_link) # 1h expiry
 └- ALWAYS 202  "If that email exists, a reset link is on the way."

2. POST /api/v1/auth/password-reset/confirm/ {token, new_password}
 └- PasswordResetToken.objects.select_related("user").get(token=...)
 (not found -> 400 "Invalid or expired reset link")
 └- if not token.is_usable() -> 400 (same generic message)
 └- token.consume()
 └- user.set_password(new_password); save(update_fields=["password"]) # HASHED
 └- 200 "Password updated. You can log in now."
```

##### Enumeration-safe 202 responses  -  kyun "agar email exist karta hai"

Yeh ek **bahut important security concept** hai. Maan lo resend/reset endpoint aisa response deta:
- email mila → "verification sent"
- email nahi mila → "no account with this email"

To attacker is response ke farak se **andaaza laga lega ki konse emails registered hain** (account enumeration). Phir woh us list pe targeted phishing/credential-stuffing kar sakta hai.

Solution: **chahe kuch bhi ho, same generic response + same status (202)** do. Code mein dekho  -  user mila ya nahi, response identical:
```python
return Response(
 {"detail": "If that email exists, a reset link is on the way."},
 status=status.HTTP_202_ACCEPTED,
)
```
`202 Accepted` semantically perfect: "humne request accept kar li, processing background mein"  -  yeh confirm nahi karta ki email bheja gaya. Attacker ko zero information leak. Email-send ka `try/except` bhi isi liye  -  agar SMTP fail bhi ho, response same rehta hai, error sirf log hota hai, user-facing behaviour nahi badalta.

`password-reset/request` mein `is_active=True` filter bhi hai  -  deactivated accounts ko reset link nahi milta.

---

#### 9. Throttling  -  `ScopedRateThrottle`

Throttling = **rate limiting**. Brute-force aur abuse rokne ke liye: kitni requests ek client ek window mein kar sakta hai.

`base.py:144`:
```python
"DEFAULT_THROTTLE_CLASSES": (
 "rest_framework.throttling.AnonRateThrottle", # anonymous users
 "rest_framework.throttling.UserRateThrottle", # logged-in users
),
"DEFAULT_THROTTLE_RATES": {
 "anon": "60/hour",
 "user": "1000/hour",
 "register": "10/hour",
 "verify_email": "20/hour",
 "password_reset": "5/hour",
 "resend_verification": "5/hour",
},
```

##### Default vs Scoped

- `AnonRateThrottle` / `UserRateThrottle` **globally** lagte hain har endpoint pe (anon 60/hr, logged-in 1000/hr). Yeh baseline protection hai.
- `ScopedRateThrottle` ek **specific scope** ko target karta hai. Sensitive auth endpoints pe tight limits chahiye. View mein:
  ```python
  class RegisterView(generics.CreateAPIView):
 throttle_classes = (ScopedRateThrottle,)
 throttle_scope = "register" # -> "register": "10/hour"
  ```
  `throttle_scope` ka string `DEFAULT_THROTTLE_RATES` ki key se match karta hai. To register ka apna 10/hour limit hai (chahe global anon 60/hr ho).

Sensitive scopes aur kyun:
- `register: 10/hour`  -  spam signups rokta hai.
- `password_reset: 5/hour`  -  reset-link spamming + enumeration attempts kam.
- `resend_verification: 5/hour`  -  email-bombing rokta hai.

##### Under the hood

Har throttle class ek **cache key** banata hai (scoped ke liye scope + client identity se  -  anon ke liye IP, user ke liye user_id) aur cache (humare case mein LocMem dev mein, ideally Redis prod mein) mein timestamps ki list rakhta hai. Har request pe purane (window-bahar) timestamps drop, baaki count. Limit cross hui to **429 Too Many Requests** + `Retry-After` header. Yeh sliding-window-ish approach hai.

**Tests mein disabled** (`test.py:28`): saare rates `100000/hour`  -  effectively off, taaki tests throttle se fail na ho. Yeh ek common pattern hai  -  production security ko test mein loosen karna (jaise MD5 hasher bhi).

Gotcha: cache LocMem hai to **per-process** count hota hai  -  multi-worker prod mein har worker ka apna count, jo limit ko effectively multiply kar deta. Isliye prod mein shared Redis cache chahiye throttling accurate hone ke liye.

---

#### 10. Signals  -  decoupled side-effects

Signal = Django ka **publish/subscribe** mechanism. Jab kuch hota hai (e.g. model save), tab registered "receivers" automatically chalte hain  -  caller ko pata bhi nahi.

`backend/apps/users/signals.py`:
```python
@receiver(post_save, sender=User)
def issue_email_verification(sender, instance, created, **kwargs):
 if not created or instance.is_email_verified:
 return
 token = EmailVerificationToken.objects.create(user=instance)
 verify_link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token.token}"
 logger.info("Issued email verification token for user_id=%s", instance.id)
 try:
 send_mail(... recipient_list=[instance.email], fail_silently=False)
 except Exception as exc:
 # Don't block signup if SMTP is down. User can /resend-verification later.
 logger.error("Failed to send verification email to %s: %s", instance.email, exc)
```

##### `post_save` on User  -  verification issue

`@receiver(post_save, sender=User)`  -  jab bhi koi `User` save ho, yeh function chalta hai. Guard:
```python
if not created or instance.is_email_verified:
 return
```
- `created` flag `post_save` deta hai  -  `True` sirf naye row pe (insert), `False` updates pe. Hum sirf **naye** users ko token bhejna chahte (har profile-update pe nahi).
- `is_email_verified` check  -  superusers (jo `create_superuser` mein already verified) ya koi already-verified case skip ho jaaye.

##### Kyun signal, view mein kyun nahi?

Register `CreateAPIView` se hota hai jo `serializer.save()` → `create()` → `User.objects.create_user()` call karta hai. Token-issuing logic ko view mein bhi daal sakte the. Par signal use karne se **decoupling** milti hai: User chahe register endpoint se bane, admin se bane, ya kisi data migration se  -  **har jagah** verification automatically trigger hoga, ek hi jagah likha logic. Single source of truth.

##### `try/except` around `send_mail`  -  recently added, non-blocking

`fail_silently=False` matlab `send_mail` exception raise karega agar SMTP fail ho. Bina try/except ke, woh exception poore signal ko, aur signal poore `create_user`/register transaction ko fail kar deta  -  **user ban hi nahi paata sirf isliye ki email server down tha**. Yeh kharab UX hai.

Isliye `try/except` lagaya gaya (MEMORY note ke hisaab se recently added): email fail ho to bas log karo, signup chalne do. User baad mein `/resend-verification/` se naya link maang sakta hai. Yeh **graceful degradation**  -  non-critical side-effect (email) critical operation (signup) ko nahi todta.

Gotcha (note karne layak): signal **synchronous** chalta hai  -  `send_mail` SMTP call signup request ko block karta hai jab tak email nahi chala jaata. Ideal world mein yeh Celery task hota (async), par MEMORY architecture ke hisaab se yeh free-tier project hai bina worker dyno ke, to inline send_mail + try/except acceptable trade-off hai.

##### `User.delete()` override  -  PROTECT FK reassignment

Yeh interview ka ek **tricky** topic hai. `signals.py` ka docstring khud bolta hai:
> Owned-group reassignment on deletion lives on `User.delete()` because PROTECT checks happen before pre_delete fires.

`apps/groups/models.py` mein `Group.owner` FK `on_delete=models.PROTECT` hai. PROTECT matlab: agar koi group is user ko owner banaye baitha hai, to user **delete hi nahi hoga**  -  Django `ProtectedError` raise karega. Yeh data-integrity ke liye hai (orphan groups na bane).

Par user delete to ho sakna chahiye  -  bas pehle uske groups handle karne padenge. Yeh logic `models.py:78` `User.delete()` override mein hai:
```python
def delete(self, *args, **kwargs):
 for group in list(self.owned_groups.all()):
 # 1. oldest OTHER admin member ko transfer
 replacement = (group.memberships.exclude(user=self)
 .filter(role=GroupMembership.ROLE_ADMIN)
 .order_by("joined_at").first())
 # 2. koi admin nahi -> oldest other member ko promote + transfer
 if replacement is None:
 replacement = group.memberships.exclude(user=self).order_by("joined_at").first()
 if replacement is not None:
 replacement.role = GroupMembership.ROLE_ADMIN
 replacement.save(update_fields=["role"])
 # 3. koi aur member hi nahi -> orphan group delete
 if replacement is None:
 group.delete()
 continue
 group.owner = replacement.user
 group.save(update_fields=["owner"])
 return super().delete(*args, **kwargs)
```

**Kyun signal mein nahi, `delete()` override mein?** Yeh subtle hai: `pre_delete` signal tab fire hota hai jab Django delete process **shuru** kar chuka hota hai. Par PROTECT constraint ka check usse **pehle** hota hai  -  to `pre_delete` ke milne se pehle hi `ProtectedError` raise ho jaata. Matlab signal mein reassign karne ka mauka hi nahi milta. Isliye reassignment ko `delete()` override mein, `super().delete()` (jo actual cascade/PROTECT check trigger karta hai) ke **call hone se pehle** karna padta hai. Ek classic ordering gotcha.

Logic 3-tier fallback hai: doosre admin ko do → na ho to oldest member ko promote karke do → koi na ho (sole member) to group hi delete. Sab `update_fields` use karta hai targeted updates ke liye.

---

#### Common galtiyan / Gotchas (consolidated)

- `default=uuid.uuid4` aur `default=secrets.token_urlsafe`  -  **function pass karo, call mat karo** (`uuid4()` nahi). Call kiya to sab rows ko same value milegi.
- `user.password = "..."` se **kabhi** plain password store mat karo  -  hamesha `set_password()`.
- `REQUIRED_FIELDS` mein `USERNAME_FIELD` ya `password` mat daalo  -  Django error dega.
- JWT payload **encrypted nahi**  -  sensitive data mat daalo, sirf integrity-protected hai.
- Logout pe access token instantly invalid nahi hota  -  max 15 min tak valid (stateless trade-off).
- Enumeration-safe responses ka matlab: error path aur success path **bilkul same** dikhne chahiye (status + message + ideally timing).
- Throttle cache prod mein **shared (Redis)** hona chahiye, warna per-worker count limit ko multiply kar deta hai.
- `AUTH_USER_MODEL` pehli migration ke baad change karna avoid karo  -  din 1 se custom User.
- PROTECT FK ke saath delete logic `delete()` override mein, `pre_delete` signal mein nahi (ordering issue).

---

#### Interview Questions + Short Answers

**Q1. Default Django User ki jagah custom User kyun banate hain, aur `AbstractBaseUser` vs `AbstractUser` mein farak?**
A: Custom User taaki email-se-login aur apni fields rakh sakein, aur kyunki `AUTH_USER_MODEL` baad mein badalna painful hai (din 1 se custom). `AbstractUser` ready User deta hai (bas extend), `AbstractBaseUser` sirf core auth machinery deta hai aur fields tum khud likhte ho  -  full control. GrindMate `AbstractBaseUser + PermissionsMixin` use karta hai email-login ke liye.

**Q2. Password hashing kaise hoti hai  -  salt aur iterations kya role play karte hain?**
A: `set_password` plain ko `pbkdf2_sha256$iterations$salt$hash` format mein store karta hai. **Salt** per-user random string hai jo rainbow-table attacks rokta hai (same password ka bhi alag hash). **Iterations** hashing ko deliberately slow banate hain taaki brute-force mehnga ho. `check_password` usi salt+algo se dobara hash karke constant-time compare karta hai.

**Q3. Access aur refresh token alag-alag kyun? Lifetimes kya rakhe aur kyun?**
A: Access (15 min) har request pe jaata hai  -  short-lived taaki chori pe jaldi bekaar ho. Refresh (7 days) sirf naya access lene ke liye, ek hi endpoint pe. Yeh stateless JWT ki revocation-difficulty ko balance karta hai: chhota attack window + user ko baar-baar login nahi karna padta.

**Q4. JWT ke teen parts kya hain, aur kya woh encrypted hote hain?**
A: header.payload.signature  -  sab base64url. Header mein algo, payload mein claims (`user_id`, `exp`), signature server ki secret se HMAC. **Encrypted nahi, sirf signed**  -  koi payload padh sakta hai par bina secret ke badal nahi sakta (integrity, not confidentiality). Isliye secret data payload mein nahi daalte.

**Q5. `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` kya karte hain, aur blacklist app kyun chahiye?**
A: Har refresh use pe naya refresh milta hai aur purana blacklist ho jaata hai. Agar chori hua purana refresh dobara use ho to blacklisted milega → reject (token-theft detection). `token_blacklist` app `OutstandingToken`/`BlacklistedToken` tables banata hai. Yeh chhota stateful exception hai  -  access tokens phir bhi pure stateless verify hote hain.

**Q6. Stateless JWT mein logout kaise kaam karta hai?**
A: Access token revoke nahi kar sakte (stateless, max 15 min mein khud expire). Logout pe **refresh token blacklist** karte hain (`RefreshToken(refresh).blacklist()`), taaki uske baad naya access na liya ja sake. Isliye logout "instant" nahi  -  purana access apni expiry tak valid.

**Q7. `validate()` aur `validate_<field>()` mein farak?**
A: `validate_<field>` single field ki standalone validation (e.g. `validate_old_password` check_password se). `validate(self, attrs)` object-level/cross-field  -  jab fields ek doosre pe depend karein (e.g. password == password_confirm). Field-level pehle chalte hain, phir object-level.

**Q8. Password-reset endpoint "if that email exists" jaisa generic message kyun deta hai?**
A: Account **enumeration** rokne ke liye. Agar response email-exist vs not-exist mein farak kare, attacker registered emails ki list bana le. Isliye dono case mein same 202 + same message  -  zero info leak. `try/except` around send_mail bhi isliye, taaki SMTP fail bhi response na badle.

**Q9. Owned-group reassignment `pre_delete` signal mein kyun nahi, `User.delete()` override mein kyun hai?**
A: `Group.owner` FK PROTECT hai. PROTECT ka check Django ke delete process aur `pre_delete` signal **se pehle** hota hai  -  to signal milne se pehle hi `ProtectedError` raise ho jaata. Isliye reassignment ko `super().delete()` call ke pehle, `delete()` override mein karna padta hai.

**Q10. `ScopedRateThrottle` global throttles se kaise alag hai?**
A: Global `AnonRateThrottle`/`UserRateThrottle` har endpoint pe lagte hain. `ScopedRateThrottle` view ke `throttle_scope` se `DEFAULT_THROTTLE_RATES` ki specific key match karke per-endpoint custom limit deta hai (e.g. `register: 10/hour`, `password_reset: 5/hour`)  -  sensitive endpoints pe tight limits.

---

#### Khud try kar (Exercises)

1. **Token decode karke dekho.** Apna access token (login response se) [jwt.io](https://jwt.io) pe paste karo. Dekho payload mein `user_id`, `exp`, aur custom `username` claim dikh raha hai. Phir payload ka koi byte badal ke wapas verify karne ki koshish karo  -  signature mismatch dekhoge. Yeh "padh sakte ho, badal nahi sakte" ko khud confirm karega.

2. **Rotation + blacklist live dekho.** Login karo (access + refresh milega). `POST /auth/token/refresh/` ko *same* refresh token se **do baar** call karo. Pehli baar naye tokens milenge; doosri baar blacklisted error. Phir `OutstandingToken`/`BlacklistedToken` tables (Django admin ya shell) mein entries check karo.

3. **Enumeration-safety verify karo.** `POST /auth/password-reset/request/` do baar maaro  -  ek registered email se, ek random non-existent se. Response body, status code, aur response time compare karo. Dono identical (202 + same message) hone chahiye. Phir socho: agar timing alag ho jaye (DB query sirf existing user pe chale) to woh bhi ek leak hoga  -  is repo mein woh risk kaisa hai?


---


## 4. LeetCode App  -  Service Layer, External API Integration & Sync Orchestration

Dekh bhai, is chapter mein hum ek aisa problem solve kar rahe hain jo har real backend dev ko kabhi na kabhi face karna padta hai: **ek third-party API jo tumhari control mein nahi hai**. Woh API kabhi slow hoga, kabhi rate-limit karega, kabhi 500 dega, aur kabhi shape badal dega. GrindMate ka pura LeetCode integration isi cheez ke around design hua hai.

LeetCode ka koi official public API nahi hai. Hum unke **unofficial GraphQL endpoint** (`leetcode.com/graphql`) se baat karte hain  -  jo Cloudflare ke peeche hai aur rate-limited hai. Iska matlab: failure ko hum *exception* nahi, *normal case* maanenge. Yeh mindset hi pure architecture ko shape karta hai.

Files jinpe poora chapter khada hai:

```
backend/apps/leetcode/
├-- services.py # API client + DTOs (pure, koi DB nahi)
├-- sync.py # orchestration + DB writes
├-- views.py # HTTP layer
├-- serializers.py # JSON in/out validation
├-- models.py # DB schema
├-- managers.py # reusable ORM queries
└-- management/commands/
 ├-- sync_leetcode.py
 └-- backfill_problems.py
```

---

#### 1. Layered Architecture  -  teen alag duniya kyun?

Sabse pehli aur sabse important cheez. Yeh teen layers ek doosre se *physically* alag hain:

| Layer | File | Job | Kya NAHI karta |
|-------|------|-----|----------------|
| **Service** | `services.py` | LeetCode se baat karna, raw JSON ko DTO mein convert karna | DB ko chhooti nahi, HTTP ka kuch nahi jaanti |
| **Orchestration** | `sync.py` | Service ko call karna, result ko DB mein persist karna, transactions | HTTP request/response nahi jaanti |
| **HTTP** | `views.py` | Request parse karna, permission check, orchestration call, JSON return | Na khud LeetCode call karti, na khud DB logic likhti |

Socho ek dam straight line hai: `views.py → sync.py → services.py → LeetCode`. Upar wali layer neeche wali ko jaanti hai, par neeche wali upar ko *bilkul* nahi.

**Kyun? Teen thos reasons:**

1. **Testability.** `services.py` mein koi Django model import hi nahi hai  -  sirf `requests` aur `dataclass`. Iska matlab tum is layer ka test bina database ke likh sakte ho, sirf HTTP mock karke (`responses` library se). Dekho test file:

```python
# tests/test_services.py
LC_URL = settings.LEETCODE_GRAPHQL_URL
```

Service tests sirf network mock karte hain. Sync tests DB use karte hain. Dono alag-alag concerns, alag-alag test files.

2. **Reuse.** `verify_account` aur `sync_account` (dono `sync.py` mein)  -  dono `services.py` ki same `fetch_profile_summary` ko call karte hain. Management command bhi `sync_account` ko call karta hai. Cron view bhi. Ek hi business logic, chaar entry points. Agar yeh logic view mein likha hota, toh har entry point pe copy-paste karna padta.

3. **Change isolation.** Kal ko LeetCode apna GraphQL schema badal de  -  sirf `services.py` change hoga. DB writes, transactions, HTTP  -  kuch nahi chhedega. Yeh boundary ek "blast radius limiter" hai.

> **Senior dev gyaan:** "Service layer" ka asli matlab yahi hai  -  *I/O ke saath baat karne wala code* aur *business decisions lene wala code* alag rakhna. `services.py` sirf "LeetCode kya bolta hai" jaanta hai. `sync.py` decide karta hai "uska kya karna hai".

---

#### 2. LeetCodeClient  -  `requests.Session` aur User-Agent ka jugaad

`services.py` line 112 se:

```python
class LeetCodeClient:
 def __init__(self, *, timeout: float = 10.0):
 self.endpoint = settings.LEETCODE_GRAPHQL_URL
 self.timeout = timeout
 self.session = requests.Session()
 self.session.headers.update(
 {
 "Content-Type": "application/json",
 "Accept": "application/json",
 # LeetCode rejects the default python-requests user-agent.
 "User-Agent": (
 "Mozilla/5.0 (compatible; GrindMateSync/1.0; +https://grindmate.app)"
 ),
 "Referer": "https://leetcode.com",
 }
 )
```

Yahan chaar cheezein samajhne layak hain:

**`requests.Session()`  -  connection reuse.** Normal `requests.get(...)` har call pe nayi TCP connection kholta hai, TLS handshake karta hai, phir band kar deta. Yeh mehnga hai. `Session` ek **connection pool** maintain karta hai  -  ek baar handshake, phir same connection pe multiple requests. Jab tum ek sync mein 30 problems backfill kar rahe ho, yeh huge difference hai. Saath hi, headers ek baar set karo, har request mein automatically lag jaate hain.

**Why `client` parameter passed around?** Notice karo `fetch_profile_summary(handle, *, client=None)`  -  agar client diya hai toh wahi use karo, warna naya banao. Iska poora point yahi hai: *ek hi Session ko reuse karo*. `sync_account` mein dekho:

```python
client = client or LeetCodeClient()
summary = fetch_profile_summary(account.handle, client=client)
recent = fetch_recent_solves(account.handle, client=client)
```

Ek client banaya, dono calls usi se. Cron backfill mein bhi ek client banakar 30 slugs ke loop mein pass karte hain. Yeh "dependency injection" ka chhota sa version hai  -  testing mein bhi kaam aata hai kyunki tum apna fake client inject kar sakte ho.

**User-Agent spoof.** LeetCode ka Cloudflare default `python-requests/2.x` user-agent dekhte hi block kar deta  -  bot samajh ke. Isliye humne ek browser-jaisa string daala. `Referer: https://leetcode.com` bhi isliye  -  kuch endpoints expect karte hain ki request "leetcode.com se aayi hai".

**`timeout=10.0`  -  yeh non-negotiable hai.** Yeh sabse common production galti hai jo log karte hain: timeout set nahi karna. Agar LeetCode hang ho jaaye aur tum timeout na do, toh tumhari request *forever* atki rahegi, gunicorn worker block ho jaayega, aur eventually tumhara pura server thread-starve ho jaayega. `timeout` ka matlab: "10 second mein response nahi aaya toh `requests.RequestException` raise kar do."

> **Gotcha:** `timeout=10` ka matlab "total 10 second" nahi hai  -  yeh hai "connect ke liye 10s YA do bytes ke beech 10s". Bada response ho toh actual total time zyada ho sakta hai. Edge case par dhyaan rakhna, par 99% cases ke liye yeh theek hai.

---

#### 3. `tenacity` ka `@retry`  -  exponential backoff

Ab asli production magic. `services.py` line 134:

```python
@retry(
 retry=retry_if_exception_type(LeetCodeRateLimited),
 stop=stop_after_attempt(3),
 wait=wait_exponential(multiplier=1, min=2, max=10),
 reraise=True,
)
def query(self, query: str, variables: dict) -> dict:
 ...
```

`tenacity` ek decorator-based retry library hai. Iss ek decorator ko tod ke samajh:

- **`retry=retry_if_exception_type(LeetCodeRateLimited)`**  -  sirf jab `LeetCodeRateLimited` raise ho tab retry karo. Baaki exceptions (jaise `LeetCodeUserNotFound`) pe retry karne ka koi point nahi  -  woh deterministic hai, dobara try karne se theek nahi hoga. Sirf *transient* failure (rate limit) retry-worthy hai. Yeh selectivity bahut zaroori hai.

- **`stop=stop_after_attempt(3)`**  -  maximum 3 attempts. Iske baad haar maan lo. Infinite retry kabhi mat karna  -  woh ek slow API ko DDoS mein badal deta hai.

- **`wait=wait_exponential(multiplier=1, min=2, max=10)`**  -  yeh **exponential backoff** hai. Har retry pe wait time double hota hai (capped):

  | Attempt fail | Wait before next |
  |--------------|------------------|
  | 1st fail | 2s (min floor) |
  | 2nd fail | 4s |
  | 3rd fail | (stop  -  no 4th) |

  Formula: `min(max, multiplier * 2^attempt)`, `min` floor ke saath clamp. **Exponential kyun, linear kyun nahi?** Kyunki rate-limit ka matlab hai "server bolega: bhai zyada aaya". Agar tum constant 2s pe hammer karte raho, toh server stressed hi rahega. Backoff progressively zyada breathing room deta hai  -  server ko recover hone ka time milta hai.

- **`reraise=True`**  -  yeh subtle par critical hai. Default mein, jab saare retries khatam ho jaate hain, tenacity apna khud ka `RetryError` raise karta hai, jo tumhare actual `LeetCodeRateLimited` ko wrap kar deta. `reraise=True` bolta hai: "saare retries fail ho gaye? Toh *asli* exception waise hi re-raise kar do." Isse upar wali `sync.py` ka `except LeetCodeAPIError` block kaam karta hai (kyunki `LeetCodeRateLimited` uska subclass hai). `reraise` ke bina yeh `except` miss ho jaata aur ek unexpected `RetryError` upar bubble karta.

> **Real-world insight:** Production mein retry tabhi achha hai jab tum *idempotent* operation retry kar rahe ho. Yahan `query()` ek read hai (GraphQL query, mutation nahi)  -  toh dobara chalana safe hai. Agar yeh ek "create payment" call hoti, toh blind retry double-charge kar deta. Hamesha poocho: "yeh operation do baar chal gaya toh kya bigdega?"

---

#### 4. Exception hierarchy  -  status code se exception mapping

`services.py` line 35:

```python
class LeetCodeAPIError(Exception):
 """Raised when LeetCode's API returns a non-recoverable error."""

class LeetCodeRateLimited(LeetCodeAPIError):
 """Raised on 429 / Cloudflare blocks - caller should back off."""

class LeetCodeUserNotFound(LeetCodeAPIError):
 """Raised when the username doesn't resolve to a real LeetCode user."""
```

Yeh ek **3-level hierarchy** hai, aur design intentional hai:

```
Exception
└-- LeetCodeAPIError (base  -  "kuch toh LeetCode side se galat hua")
 ├-- LeetCodeRateLimited (transient  -  retry karne layak)
 └-- LeetCodeUserNotFound  (permanent  -  user hi nahi hai)
```

**Base class kyun?** `sync.py` mein dekho  -  woh sirf `except LeetCodeAPIError` likhta hai. Iska matlab: koi bhi LeetCode-related failure (rate limit, user not found, network error, GraphQL error)  -  sab ek hi catch mein pakde jaate hain. Caller ko har specific type alag se handle nahi karna padta. Par jab *zaroorat* ho, toh specific subclass bhi catch kar sakta hai (jaise retry decorator sirf `LeetCodeRateLimited` pakadta hai).

Ab `query()` ka status-code mapping dekho, line 150:

```python
if response.status_code in (429, 403):
 raise LeetCodeRateLimited(f"Rate limited (HTTP {response.status_code}).")
if response.status_code >= 500:
 raise LeetCodeAPIError(f"LeetCode {response.status_code}.")
if response.status_code != 200:
 raise LeetCodeAPIError(
 f"Unexpected status {response.status_code}: {response.text[:200]}",
 )

body = response.json()
if body.get("errors"):
 raise LeetCodeAPIError(f"GraphQL errors: {body['errors']}")
return body.get("data", {})
```

Yeh order matter karta hai  -  yeh ek decision tree hai:

1. **429 / 403 → `LeetCodeRateLimited`.** 429 toh classic "Too Many Requests" hai. Par 403 ko bhi rate-limit treat kiya  -  kyunki Cloudflare jab tumhe bot samajh ke block karta hai toh 403 deta hai, aur thodi der ruk ke retry karne se woh aksar clear ho jaata. Yeh dono retry-worthy hain (decorator inhe pakdega).
2. **5xx → `LeetCodeAPIError`.** Server-side error. Yeh `LeetCodeRateLimited` nahi hai, toh **retry nahi hoga** (decorator sirf rate-limit pe retry karta hai). Conscious choice  -  500 ka matlab LeetCode side pe bug/outage hai, retry se theek nahi hoga.
3. **Koi aur non-200 → `LeetCodeAPIError`** with first 200 chars of body. `[:200]` isliye taaki error log mein pura HTML page na ghuse.
4. **200 par GraphQL `errors` array present** → `LeetCodeAPIError`. **Yeh GraphQL ka classic trap hai:** GraphQL hamesha HTTP 200 deta hai, even jab query fail ho! Error body ke andar `"errors": [...]` mein hota hai. Agar tum sirf status code check karte aur `errors` ignore karte, toh garbage data DB mein chala jaata. Isliye explicit check.
5. **Network exception** (line 147)  -  `requests.RequestException` (timeout, DNS fail, connection refused) ko bhi `LeetCodeAPIError` mein wrap kar diya, `from exc` ke saath (original traceback preserve hota hai). Toh caller ko sirf ek family of exceptions handle karni padti hai  -  `requests` ka exception leak nahi hota.

> **Design principle:** Service layer LeetCode ki saari I/O failures ko *apni* exception vocabulary mein translate kar deta hai. Caller ko `requests.Timeout` ya GraphQL ke internals ki tension nahi leni  -  usko sirf `LeetCodeAPIError` family pata honi chahiye. Yeh "leaky abstraction" se bachata hai.

---

#### 5. DTOs  -  frozen dataclasses jo API shape ko model se decouple karte hain

`services.py` line 50:

```python
@dataclass(frozen=True)
class ProfileSummary:
 handle: str
 ranking: int | None
 total_solved: int
 easy_solved: int
 medium_solved: int
 hard_solved: int

@dataclass(frozen=True)
class RecentSolve:
 title_slug: str
 title: str
 solved_at: datetime  # tz-aware UTC

@dataclass(frozen=True)
class ProblemMeta:
 title_slug: str
 title: str
 difficulty: str
 topic_tags: list[str]
 is_premium: bool
 leetcode_id: int | None
```

**DTO = Data Transfer Object.** Yeh service layer aur uske callers ke beech ka *contract* hai. Service raw GraphQL JSON ko in clean Python objects mein parse karke deta hai.

**`frozen=True` kyun?** Yeh dataclass ko immutable bana deta hai  -  ek baar bana, attributes change nahi kar sakte (`summary.ranking = 5` → `FrozenInstanceError`). Reasons:
- DTO sirf "data carry karne ke liye" hai, mutate karne ke liye nahi. Immutability accidental modification se bachati hai.
- Frozen dataclass hashable hoti hai (set/dict key mein use ho sakti hai)  -  though yahan zaroorat nahi, ek nice property hai.
- Code clarity: jo banda DTO use kar raha hai woh confident reh sakta hai "yeh value sync ke beech mein badlegi nahi."

**Decoupling ka asli value:** Dekho `fetch_profile_summary` (line 168) GraphQL ke ugly nested JSON ko kaise clean karta hai:

```python
matched = data.get("matchedUser")
if not matched:
 raise LeetCodeUserNotFound(f"No LeetCode user found for handle {handle!r}.")

counts = {
 row["difficulty"].lower(): row["count"]
 for row in matched["submitStats"]["acSubmissionNum"]
}

return ProfileSummary(
 handle=matched["username"],
 ranking=(matched.get("profile") or {}).get("ranking"),
 total_solved=counts.get("all", 0),
 easy_solved=counts.get("easy", 0),
 ...
)
```

GraphQL deta hai `submitStats.acSubmissionNum` mein ek *list* of `{difficulty, count}` rows  -  ek "All" bucket plus easy/medium/hard. Service yeh list-of-dicts ko ek flat `counts` dict mein badalta hai, phir DTO banata hai. **Ab tumhare `sync.py` ko LeetCode ke JSON shape ki bilkul khabar nahi.** Kal LeetCode `acSubmissionNum` ka naam badal de  -  sirf yeh ek function change hoga, `ProfileSummary` ka shape same rahega, `sync.py` untouched.

`(matched.get("profile") or {}).get("ranking")`  -  yeh defensive pattern dhyaan se dekho. Agar `profile` key `None` ho (LeetCode kabhi-kabhi `null` deta hai), toh `None.get()` crash karta. `or {}` se woh empty dict ban jaata aur safely `None` return hota. Real-world flaky API ka classic defensive code.

`fetch_recent_solves` (line 191) timestamp handling dekho:

```python
ts = int(row["timestamp"]) # LeetCode unix-second STRING bhejta hai
RecentSolve(..., solved_at=datetime.fromtimestamp(ts, tz=UTC))
```

LeetCode timestamp ko **string** mein bhejta hai, isliye `int()` cast. Aur `tz=UTC` zaroori  -  naked `datetime.fromtimestamp(ts)` server ke local timezone mein deta, jo bug hota. Hamesha tz-aware UTC store karo. (Yeh `USE_TZ=True` Django ke saath consistent rehta.)

`fetch_problem_meta` (line 215) mein `questionFrontendId` ko `int()` mein cast karte time `try/except ValueError` hai  -  kyunki kuch problems ka frontend ID weird ho sakta hai (e.g. non-numeric). Defensive again  -  ek problem ka bad ID poore sync ko nahi giraana chahiye.

> **Why not just return raw dict?** Raw dict return karne se har caller ko keys yaad rakhni padti (`data["matchedUser"]["submitStats"]...`), typo crash karta runtime pe, aur IDE autocomplete nahi deta. DTO se: typed attributes, autocomplete, ek jagah validation. Yeh "stringly-typed" code se "strongly-typed" code ka jump hai.

---

#### 6. `sync.py` orchestration  -  aur Render-timeout wali asli engineering kahani

Ab pure chapter ka dil. Yeh samajhna ki **`verify_account` aur `sync_account` alag kyun hain**, aur **`defer_meta` kyun exist karta hai**  -  yeh ek real production constraint se nikla design hai.

##### Render ka 60-second timeout problem

GrindMate free tier pe Render pe deploy hota hai. Render ka gunicorn worker har HTTP request ke liye **~60 second hard timeout** rakhta hai  -  agar request 60s mein respond nahi karti, woh kill ho jaati, user ko 502 milta.

Ab socho user pehli baar apna handle link karta hai (`POST /account/`). Naive approach hoti:
1. Profile fetch karo (1 LeetCode call)
2. Recent 50 solves fetch karo (1 call)
3. Har solve ke liye problem metadata fetch karo (**50 LeetCode calls!**)

Agar har call ~1-2s (retries ke saath aur zyada), toh 50 calls = **60-100+ second**. Render isko maar dega. User ka handle "link" hi nahi hoga. Disaster.

**Solution  -  do alag entry points + lazy backfill.**

##### `verify_account`  -  fast path (link endpoint ke liye)

`sync.py` line 132:

```python
def verify_account(account, *, client=None):
 """Fast path: single profile fetch to verify the handle and refresh stats.
 Used by the link-handle endpoint - no per-problem network calls, so it
 completes in ~2s and fits inside any reasonable HTTP timeout."""
 client = client or LeetCodeClient()
 try:
 summary = fetch_profile_summary(account.handle, client=client)
 except LeetCodeAPIError as exc:
 return _record_failure(account, exc)

 _apply_summary(account, summary)
 account.save()
 return SyncResult(new_solves=0, total_solved=summary.total_solved, problems_resolved=0)
```

**Sirf ONE LeetCode call.** Handle valid hai? Aggregates refresh ho gaye? Bas. ~2 second mein khatam. `views.py` ka `POST /account/` isi ko call karta hai (line 61). Recent solves yahan touch hi nahi karte.

##### `sync_account`  -  full sync, par smart

`sync.py` line 159:

```python
def sync_account(account, *, client=None):
 client = client or LeetCodeClient()
 try:
 summary = fetch_profile_summary(account.handle, client=client)
 recent = fetch_recent_solves(account.handle, client=client)
 except LeetCodeAPIError as exc:
 return _record_failure(account, exc)

 new_solves = 0
 problems_resolved = 0

 with transaction.atomic():
 for solve in recent:
 problem = Problem.objects.filter(title_slug=solve.title_slug).first()
 if problem is None:
 problem = upsert_problem(
 solve.title_slug,
 defer_meta=True, # <-- yeh hai magic
 fallback_title=solve.title,
 )
 problems_resolved += 1

 _log, created = SubmissionLog.objects.get_or_create(
 user=account.user,
 problem=problem,
 solved_at=solve.solved_at,
 defaults={"source": SubmissionLog.SOURCE_AUTO},
 )
 if created:
 new_solves += 1

 _apply_summary(account, summary)
 account.save()

 return SyncResult(new_solves=new_solves, ...)
```

Notice: sirf **2 LeetCode calls total** (profile + recent), chaahe 50 solves ho. Loop ke andar koi network call nahi.

##### `defer_meta`  -  lazy backfill ka core

`upsert_problem` line 39:

```python
def upsert_problem(slug, *, client=None, defer_meta=False, fallback_title=None):
 problem = Problem.objects.filter(title_slug=slug).first()
 if problem:
 return problem # already cached, done

 if defer_meta:
 return Problem.objects.create( # PLACEHOLDER row, koi API call nahi
 title_slug=slug,
 title=fallback_title or slug.replace("-", " ").title(),
 difficulty="", # <-- khaali = "abhi backfill hona baaki hai"
 topic_tags=[],
 is_premium=False,
 )

 meta = fetch_problem_meta(slug, client=client) # full path: ek API call
 problem, _ = Problem.objects.update_or_create(
 title_slug=meta.title_slug,
 defaults={"title": meta.title, "difficulty": meta.difficulty or "easy", ...},
 )
 return problem
```

`defer_meta=True` ke saath: ek **placeholder** `Problem` row banti hai jiska `difficulty=""` (empty string). Koi LeetCode call nahi. Title bhi slug se derive kar liya (`two-sum` → `Two Sum`) ya recent-solves se mila `fallback_title` use kiya. Iska matlab `SubmissionLog` ke liye ek `Problem` FK mil gaya, aur sync 2 calls mein khatam.

`difficulty=""` ek **sentinel value** hai  -  "yeh row abhi adhoori hai, isko backfill karna baaki hai." Real difficulty hamesha `easy/medium/hard` hota hai, blank kabhi nahi. Toh empty string se hum incomplete rows identify kar sakte hain.

##### Backfill  -  adhoori rows baad mein bharna

`backfill_problem_meta` (line 80) aur cron/command in placeholder rows ko nightly fill karte hain:

```python
def backfill_problem_meta(slug, *, client=None):
 meta = fetch_problem_meta(slug, client=client)
 problem, _ = Problem.objects.update_or_create(
 title_slug=slug,
 defaults={"title": meta.title, "difficulty": meta.difficulty or "easy", ...},
 )
 return problem
```

Aur kaun call karta hai? `Problem.objects.filter(difficulty="")`  -  yani saare placeholder. `CronBackfillProblemsView` (views.py line 199) aur `backfill_problems` command dono yahi query use karte hain.

**Poora flow ek diagram mein:**

```
User links handle  →  POST /account/  →  verify_account()  →  1 call, ~2s ✓
 (no solves yet)

Cron every 6h / "Sync now"  →  sync_account()  →  2 calls
 └- new problems: difficulty="" placeholder rows
 (NO per-problem call)

Nightly cron  →  CronBackfillProblemsView  →  backfill_problem_meta() × 30
 └- difficulty="" rows ko full metadata se bharo
```

> **Yeh asli engineering decision hai.** "60s timeout" ek hard external constraint tha. Iska solution architecture mein bake kiya gaya: *kaam ko unke latency-sensitivity ke hisaab se split karo*. Synchronous user-facing path (link/sync) ko 2 calls tak bounded rakha. Slow-but-not-urgent kaam (metadata enrichment) ko background cron pe push kiya, capped batches mein. Yeh "eventual consistency" ka ek practical example hai  -  data thodi der ke liye incomplete rehta hai (difficulty blank), par user ka link kabhi fail nahi hota.

##### `_apply_summary` aur `_record_failure`  -  helper functions

`_apply_summary` (line 106) sirf DTO ke fields ko account object pe copy karta hai aur status OK karta. `_record_failure` (line 118) failure pe status `FAILED` set karta, error message (1000 chars tak truncated) save karta, aur ek error-carrying `SyncResult` return karta:

```python
def _record_failure(account, exc):
 logger.warning("LeetCode call failed for %s: %s", account.handle, exc)
 account.sync_status = SyncStatus.FAILED
 account.last_sync_error = str(exc)[:1000]
 account.last_synced_at = timezone.now()
 account.save(update_fields=["sync_status", "last_sync_error", "last_synced_at"])
 return SyncResult(new_solves=0, total_solved=account.total_solved, problems_resolved=0, error=str(exc))
```

`update_fields=[...]` important hai  -  yeh Django ko bolta hai "sirf yeh teen columns update karo, baaki SQL UPDATE mein touch mat karo." Performance optimization + race-safety (doosre fields stale value se overwrite nahi honge). `str(exc)[:1000]`  -  error message ko cap kiya taaki ek giant traceback DB column ko na bhar de.

In dono helpers ka point: sync ke do paths (`verify` aur `sync`) mein same success/failure logic repeat ho raha tha  -  DRY principle se extract kar diya.

---

#### 7. `transaction.atomic()`  -  partial write se bachna

`sync_account` ka pura DB-writing loop `with transaction.atomic():` ke andar hai. Yeh **kyun** critical hai?

Socho 50 solves process ho rahe hain. 30th pe `SubmissionLog.objects.get_or_create` koi error de de (maan lo DB connection blink). `atomic()` ke bina: pehle 29 logs commit ho chuke, account aggregates update nahi hue, problems half-resolved. **Inconsistent state.** Account bolega "total_solved=200" par sirf 29 naye logs hain.

`atomic()` ke saath: woh poora block ek **single transaction** hai. Ya toh saare 50 logs + account update ek saath commit honge, ya kuch bhi commit nahi hoga (exception pe pura **rollback**). Database hamesha consistent rehta hai  -  all-or-nothing.

**Under the hood:** `transaction.atomic()` block enter karte hi Django `BEGIN` (ya savepoint) issue karta hai. Block clean exit kare → `COMMIT`. Block ke andar exception escape kare → `ROLLBACK`. Yeh PostgreSQL/SQLite ke native transaction semantics use karta hai.

Dhyaan do: `summary` aur `recent` fetch (network calls) `atomic()` ke **bahar** hain. **Yeh deliberate hai.** Network call slow hai  -  usko transaction ke andar rakhne ka matlab hota: poori network duration tak DB lock/connection hold karna. Pattern: *pehle saara slow I/O karo, phir transaction ke andar sirf fast DB writes karo.* Transaction ko short rakhna ek important performance rule hai.

> **Gotcha:** `atomic()` ke andar exception pakad ke (`except`) usko swallow mat karna aur phir aur DB queries mat chalana  -  transaction "broken" state mein chala jaata hai aur agli query `TransactionManagementError` degi. Yahan code exceptions ko `atomic()` ke bahar handle karta hai (network errors), isliye safe hai.

---

#### 8. `get_or_create` vs `update_or_create`

Dono `sync.py` mein use hue hain, aur difference samajhna zaroori hai:

| | `get_or_create` | `update_or_create` |
|--|-----------------|--------------------|
| Row milti hai | use karo as-is | **`defaults` se update** karo |
| Row nahi milti | `defaults` se banao | `defaults` se banao |
| Returns | `(obj, created_bool)` | `(obj, created_bool)` |

**`sync_account` mein `get_or_create` (line 192):**

```python
_log, created = SubmissionLog.objects.get_or_create(
 user=account.user,
 problem=problem,
 solved_at=solve.solved_at,
 defaults={"source": SubmissionLog.SOURCE_AUTO},
)
if created:
 new_solves += 1
```

Yahan `get_or_create` perfect hai: agar yeh exact solve (`user + problem + solved_at`) pehle se logged hai, kuch mat karo  -  yeh ek duplicate sync hai, naya event nahi. `created` flag se hum *naye* solves count karte hain. Yeh **idempotency** deta hai: same sync 10 baar chalao, count nahi badhega.

**`upsert_problem`/`backfill_problem_meta` mein `update_or_create` (line 67, 93):**

```python
problem, _ = Problem.objects.update_or_create(
 title_slug=meta.title_slug,
 defaults={"difficulty": meta.difficulty or "easy", "topic_tags": meta.topic_tags, ...},
)
```

Yahan `update_or_create` chahiye kyunki: agar `Problem` placeholder ke roop mein pehle se hai (`difficulty=""`), toh hum usko **overwrite karke fresh metadata se update** karna chahte hain. `get_or_create` hota toh placeholder waise hi reh jaata. Backfill ka pura point hi "existing row ko update karna" hai.

**Race notes (important!):** `get_or_create` atomic *nahi* hai by default. Andar do steps hain: `SELECT` (milta hai?) phir `INSERT` (nahi mila toh). Do concurrent requests dono "nahi mila" dekh ke dono `INSERT` try kar sakte → `IntegrityError` (agar unique constraint hai). Django docs bolte hain: `get_or_create` ko **sirf tab use karo jab field pe unique constraint ho**  -  taaki race mein doosra INSERT fail ho aur Django uss `IntegrityError` ko handle kar sake (woh `get()` retry karta hai). Yahan `SubmissionLog` pe `UniqueConstraint(user, problem, solved_at)` hai (models.py line 132)  -  toh yeh safe hai. Bina unique constraint ke duplicate rows ban jaate.

`defaults` ka role: yeh woh fields hain jo **lookup mein use nahi hote** par create/update pe set hote. Notice `source` `defaults` mein hai, par `user/problem/solved_at` nahi  -  kyunki woh lookup keys hain (matching ke liye), `source` sirf naya banate time ka data hai.

---

#### 9. `SyncResult` dataclass  -  error ko surface karna, swallow nahi

`sync.py` line 31:

```python
@dataclass
class SyncResult:
 new_solves: int
 total_solved: int
 problems_resolved: int
 error: str | None = None
```

Yeh ek **structured return type** hai. Har sync function isko return karta hai  -  success mein bhi, failure mein bhi (`_record_failure` bhi `SyncResult` deta, bas `error` field set karke).

**Yeh frozen kyun nahi?** Yeh DTO `services.py` ke immutable-by-design DTOs se thoda alag intent rakhta  -  yeh ek result aggregator hai. Par practically isko bhi koi mutate nahi karta, toh `frozen=True` daala ja sakta tha. Yeh ek minor inconsistency hai codebase mein.

**Asli philosophy  -  error kabhi silently swallow mat karo.** Notice: sync functions exception ko upar throw nahi karte (woh `except LeetCodeAPIError` mein pakad lete). Par woh failure ko **chupate bhi nahi**  -  `error` field mein daal ke caller ko de dete. Caller decide karta kya karna hai:

- `views.py` `SyncAccountView` (line 96): `error` ko JSON response mein daal deta, user dekh leta.
- `views.py` `POST /account/` (line 62): agar `result.error`, toh HTTP 202 (Accepted) deta  -  "handle link ho gaya par verify nahi hua"  -  `LeetCodeAccountSerializer` ke saath.
- `sync_leetcode` command (line 56): `error` ho toh red `stderr` pe print karta.
- `CronSyncAllView` (line 154): `error` se `failed` counter badhata.

> **Yeh "errors as values" pattern hai** (Go/Rust se influenced). Exception throw karna ek option hai, par yahan failure ek *expected* outcome hai (flaky API yaad hai?), toh usko data ki tarah return karna zyada natural hai. Caller ko `try/except` nahi likhna padta, woh bas `if result.error` check karta. Lekin  -  *kabhi* `error` ko `None` chhod ke chup nahi reh jaate. Yeh "fail loud" principle hai.

---

#### 10. Cron endpoints  -  shared secret, JWT kyun nahi

`views.py` line 121  -  `CronSyncAllView`:

```python
class CronSyncAllView(APIView):
 permission_classes = (permissions.AllowAny,)
 throttle_classes = ()  # external scheduler should not be throttled

 def post(self, request):
 expected = settings.CRON_SHARED_SECRET
 if not expected:
 return Response(
 {"detail": "Cron sync is disabled (CRON_SHARED_SECRET not set)."},
 status=status.HTTP_503_SERVICE_UNAVAILABLE,
 )

 provided = request.headers.get("X-Cron-Token", "")
 if not secrets.compare_digest(provided.encode(), expected.encode()):
 return Response({"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)

 accounts = list(LeetCodeAccount.objects.exclude(sync_status=SyncStatus.UNVERIFIED))
 synced = failed = 0
 for account in accounts:
 result = sync_account(account)
 if result.error:
 failed += 1
 else:
 synced += 1
 ...
```

**Architecture recall:** GrindMate free tier pe **koi Celery worker dyno nahi** hai (woh paid hota). Toh background scheduled sync **GitHub Actions cron** se hota  -  GitHub har 6 ghante ek workflow chalata jo yeh endpoint hit karta. Yeh ek *external* caller hai, jiske paas koi user session/JWT nahi hai.

**JWT kyun nahi?**
- JWT ek *user* ko represent karta. Cron koi user nahi  -  woh "system" hai. JWT token banane ke liye kisi user ke credentials chahiye, jo CI mein store karna awkward aur fragile (token expire hota).
- Cron ko *saare* accounts sync karne hain, kisi ek user ke nahi. JWT-based per-user auth yahan fit hi nahi.
- Shared secret simple hai: ek env var (`CRON_SHARED_SECRET`) backend pe, same value GitHub Actions secret mein. Bas. No expiry, no refresh, no user.

**`permission_classes = (AllowAny,)`**  -  DRF ki default JWT auth bypass karke, hum **khud** header check karte hain. Yeh deliberate hai  -  endpoint "publicly reachable" hai par token ke bina kuch nahi karta.

**`secrets.compare_digest`  -  timing attack se bachav.** Yeh sabse subtle security point hai. Normal `provided == expected` comparison **short-circuit** karta hai  -  pehle mismatched char pe ruk jaata. Attacker is timing difference ko measure karke (microseconds) token ko *char-by-char* guess kar sakta hai ("yeh char sahi tha kyunki response thoda slow aaya"). `secrets.compare_digest` **constant-time** comparison karta  -  chaahe pehla char galat ho ya aakhri, same time leta. Secret/token/password compare karne ka yeh hamesha sahi tareeka hai.

**`.encode()` kyun?** `compare_digest` bytes (ya pure-ASCII str) maangta. `.encode()` se string → UTF-8 bytes.

**`if not expected:` → 503.** Agar secret set hi nahi (dev/misconfig), endpoint disabled. Yeh "fail closed" hai  -  secret missing ho toh by default kuch allow mat karo, na ki accidentally open chhod do.

**`throttle_classes = ()`**  -  DRF mein global rate-throttling lagi ho sakti (anonymous users ke liye). Cron ko usse exempt kiya  -  warna scheduled call kabhi-kabhi throttle ho ke fail ho jaata. Trusted caller (token-verified) ko throttle karna pointless hai.

**`CronBackfillProblemsView`** (line 163) same security pattern follow karta, plus ek extra: `limit` cap.

```python
limit = max(1, min(limit, 100))
pending = list(
 Problem.objects.filter(difficulty="").values_list("title_slug", flat=True)[:limit]
)
```

`max(1, min(limit, 100))`  -  limit ko 1..100 range mein clamp. Kyun? **Wahi timeout story.** Har backfill = 1 LeetCode call. Agar 5000 placeholder rows hain aur tum sab ek request mein process karne lagte, request timeout ho jaayegi. Toh per-invocation cap, aur cron baar-baar chala ke batches mein khatam karta. `values_list(..., flat=True)`  -  sirf slug column fetch karta (poora object nahi), memory/query efficient.

> **Gotcha:** Note `CronBackfillProblemsView` ke imports function ke andar hain (`from .models import Problem`). Yeh aksar circular-import bachne ke liye hota hai, par yahan top-level import bhi chal jaata  -  minor style inconsistency.

---

#### 11. Management commands  -  `manage.py sync_leetcode --all` ki internals

Django commands `BaseCommand` se inherit karte. `sync_leetcode.py` line 15:

```python
class Command(BaseCommand):
 help = "Manually sync one or all linked LeetCode accounts."

 def add_arguments(self, parser) -> None:
 group = parser.add_mutually_exclusive_group(required=True)
 group.add_argument("--user", help="Sync the LeetCode account for this username.")
 group.add_argument("--handle", help="Sync the LeetCode account with this handle.")
 group.add_argument("--all", action="store_true", help="Sync every linked account.")

 def handle(self, *args, **options) -> None:
 ...
```

**Mechanics:**
- **`help`**  -  `python manage.py help sync_leetcode` pe dikhta.
- **`add_arguments(parser)`**  -  yeh CLI args define karta. `parser` Python ka standard `argparse` hai. `add_mutually_exclusive_group(required=True)` ka matlab: `--user`, `--handle`, `--all` mein se **exactly ek** dena hi padega  -  do diye toh argparse khud error dega. Smart UX: tum ek user, ek handle, ya sab  -  par ek hi mode chuno.
- **`action="store_true"`**  -  `--all` ek flag hai (value nahi leta). Diya toh `options["all"] = True`.
- **`handle(*args, **options)`**  -  command ka entry point. `manage.py sync_leetcode --all` chalane pe Django yeh dhoondta hai, `add_arguments` se args parse karta, phir `handle` ko `options={"all": True, "user": None, "handle": None}` ke saath call karta.

**Output styling:** `self.stdout.write(...)` print ki jagah (Django capture/test kar sakta), aur `self.style.SUCCESS(...)` / `self.style.ERROR(...)` colored output dete (green/red terminal mein). Errors `self.stderr` pe jaate. Line 57-62:

```python
if result.error:
 self.stderr.write(self.style.ERROR(f" ✗ {result.error}"))
else:
 self.stdout.write(self.style.SUCCESS(f" ✓ {result.new_solves} new (total {result.total_solved})"))
```

**`CommandError`** (line 38)  -  jab user galat handle/user de, hum `raise CommandError(...)` karte. Django isko gracefully pakad ke clean error print karta aur exit code 1 deta  -  full ugly traceback nahi dikhata. Yeh CLI ka "user-facing error" hai vs "programmer bug" (jo traceback deta).

**Command vs Cron endpoint  -  dono `sync_account` use karte!** Notice  -  yeh `sync.py` ki orchestration layer ka reuse hai. Command local/manual run ke liye, cron endpoint scheduled remote run ke liye, par dono *exact same* `sync_account` call karte. Yeh fir wahi layering ka fayda. `--all` command ka query `LeetCodeAccount.objects.exclude(sync_status=SyncStatus.UNVERIFIED)`  -  bilkul `CronSyncAllView` jaisa.

**`backfill_problems` command extra:** `--sleep` arg (default 1.0s)  -  har LeetCode call ke beech `time.sleep()`. Yeh **manual rate-limit margin** hai  -  taaki hum LeetCode ko flood na karein aur 429 na khaayein. Cron view mein sleep nahi (kyunki woh sirf 30-cap karta), par local bulk command mein politeness ke liye sleep hai.

```python
for slug in slugs:
 try:
 backfill_problem_meta(slug, client=client)
 ok += 1
 except LeetCodeAPIError as exc:
 self.stderr.write(self.style.ERROR(f"  x {slug}: {exc}"))
 fail += 1
 time.sleep(options["sleep"])
```

Dekho: ek slug fail kare toh poora command nahi rukta  -  `except` se skip, count, aage badho. "Best-effort batch processing." Ek bad problem baaki sabko nahi rokta.

---

#### 12. Models  -  schema decisions

`models.py`  -  har choice ke peeche reason hai.

##### `TextChoices`  -  `SyncStatus` aur `Difficulty`

```python
class SyncStatus(models.TextChoices):
 PENDING = "pending", "Pending"
 OK = "ok", "OK"
 FAILED = "failed", "Failed"
 UNVERIFIED = "unverified", "Unverified"
```

`TextChoices` ek enum hai jo DB mein **string** store karta. `PENDING = "pending", "Pending"` ka pehla value DB mein jaata (`"pending"`), doosra human-readable label (admin/forms mein dikhta). Code mein `SyncStatus.OK` likho  -  typo-safe, IDE autocomplete, aur DB mein readable string (integer codes ki tarah cryptic nahi). `sync.py` mein `account.sync_status = SyncStatus.OK`  -  clean.

##### `LeetCodeAccount`  -  `OneToOneField`

```python
user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leetcode_account")
```

**OneToOne kyun, ForeignKey kyun nahi?** Ek user ka **sirf ek** LeetCode handle hota. `OneToOneField` DB level pe yeh enforce karta (unique constraint on `user_id`). `related_name="leetcode_account"` se `user.leetcode_account` se reverse access milta (FK mein `user.leetcode_account_set.all()` hota  -  list). `on_delete=CASCADE`  -  user delete hua toh uska account bhi delete (orphan data nahi).

`settings.AUTH_USER_MODEL` use kiya, direct `User` import nahi  -  yeh Django best practice hai jab custom user model ho (GrindMate ka apna user model hai). Hardcode karte toh swap karna mushkil hota.

`@property is_verified`  -  ek computed property, DB column nahi. `sync_status != UNVERIFIED`. Serializer ise `read_only` field ki tarah expose karta (serializers.py line 11).

##### `Problem`  -  cached catalog

```python
title_slug = models.SlugField(max_length=128, unique=True)
difficulty = models.CharField(max_length=8, choices=Difficulty.choices)
topic_tags = models.JSONField(default=list, blank=True)
...
indexes = [models.Index(fields=["difficulty"])]
```

`title_slug` `unique=True`  -  yeh natural key hai. `upsert_problem` isi pe lookup karta. Iss unique constraint ki wajah se `get_or_create`/`update_or_create` race-safe hote (point 8 yaad hai).

`topic_tags = JSONField(default=list)`  -  tags ek list hai (`["array", "hash-table"]`). Alag table banane ke bajaye JSON column  -  kyunki tags pe hum query nahi karte, sirf display karte. Simple. `default=list` (`default=[]` nahi!)  -  **mutable default gotcha.** Agar `default=[]` likhte, toh saare rows ek hi list object share karte (Python ka classic mutable-default-arg bug). `list` (callable) pass karne se har row apni nayi list banati.

`Index(fields=["difficulty"])`  -  leaderboard/filter "by difficulty" queries fast karta. `views.py` `SubmissionListView` mein `filterset_fields = ("source", "problem__difficulty")` hai  -  yeh index us filter ko speed deta.

##### `SubmissionLog`  -  composite index + UniqueConstraint

```python
problem = models.ForeignKey(Problem, on_delete=models.PROTECT, related_name="submissions")
solved_at = models.DateTimeField()
...
class Meta:
 indexes = [
 models.Index(fields=["user", "-solved_at"], name="submission_user_date_idx"),
 models.Index(fields=["solved_at"]),
 ]
 constraints = [
 models.UniqueConstraint(fields=["user", "problem", "solved_at"], name="unique_user_problem_solved_at"),
 ]
```

**`on_delete=models.PROTECT` on `problem`  -  yeh sabse interesting choice hai.** User pe `CASCADE` hai (user gaya toh logs gaye, makes sense). Par `Problem` pe **PROTECT**  -  matlab agar koi `SubmissionLog` ek `Problem` ko reference karta hai, toh woh `Problem` **delete nahi ho sakta** (Django `ProtectedError` raise karega).

**Kyun?** `Problem` ek shared catalog hai  -  multiple users ke logs usko point karte. Agar galti se (ya kisi cleanup script se) ek Problem delete ho jaye, toh CASCADE hota toh **saare users ke woh solves bhi delete** ho jaate  -  silent data loss! PROTECT ek **safety net** hai: "yeh Problem kahin use ho raha hai, isko delete mat karne do." Yeh accidental cascade-delete se bachata. Shared/reference data pe PROTECT ek conscious defensive pattern hai.

**Composite index `(user, -solved_at)`**  -  yeh leaderboard aur "is hafte ke solves" queries ka backbone hai. `managers.py` dekho  -  `this_week()`, `today()` sab `user` filter + `solved_at` range pe queries karte. Yeh composite index us exact access pattern ko match karta. `-solved_at` (descending) isliye kyunki hum aksar "latest first" order karte (`ordering = ("-solved_at",)`), aur descending index us sort ko bina extra sort-step ke serve karta.

**`UniqueConstraint(user, problem, solved_at)`**  -  comment khud bolta: "A user solving the same problem twice in the same minute is a duplicate sync, not a new event." Yeh `sync_account` ke `get_or_create` ko de-duplication power deta  -  same sync dobara chale toh duplicate log nahi banta. Aur `ManualSubmissionView` (views.py line 249) isi constraint ke `IntegrityError` ko pakad ke HTTP 409 (Conflict) deta  -  "tumne yeh solve already log kiya." Constraint ek hi jagah define, do jagah enforce.

---

#### Common Galtiyan / Gotchas (consolidated)

1. **External call pe `timeout` na dena**  -  server thread leak ho jaata. Hamesha set karo.
2. **GraphQL ka `errors` ignore karna**  -  GraphQL fail hone par bhi HTTP 200 deta. `body.get("errors")` check karna *mandatory*.
3. **Blind retry on every error**  -  sirf transient (rate-limit) retry karo, `LeetCodeUserNotFound` jaise permanent errors pe nahi. Aur mutations (non-idempotent) ko blind retry mat karo.
4. **Token compare `==` se karna**  -  timing attack. Hamesha `secrets.compare_digest`.
5. **`default=[]` in JSONField**  -  mutable default shared ho jaata. `default=list` use karo.
6. **`get_or_create` bina unique constraint ke**  -  race mein duplicate rows. Unique constraint zaroori.
7. **Network call `transaction.atomic()` ke andar**  -  DB connection/lock slow network tak hold. Slow I/O transaction se bahar rakho.
8. **Naked `datetime.fromtimestamp(ts)`**  -  server local tz mein convert hota. Hamesha `tz=UTC`.
9. **Long-running sync ko ek synchronous request mein karna**  -  Render/gunicorn timeout maar dega. Fast path + deferred backfill mein split karo.

---

#### Interview Questions + short answers

**Q1: Service layer aur orchestration layer alag kyun rakhte hain?**
A: Service (`services.py`) pure I/O hai  -  koi DB/HTTP nahi, isliye network-mock se akele testable, aur multiple callers reuse karte. Orchestration (`sync.py`) business decisions + DB writes karta. Alag rakhne se testability, reuse, aur change isolation (LeetCode schema change → sirf service touch) milte.

**Q2: `verify_account` aur `sync_account` mein farak kya, aur dono kyun?**
A: `verify_account` sirf 1 LeetCode call (profile) karta  -  ~2s, link endpoint ke liye, taaki Render ke 60s timeout mein fit ho. `sync_account` 2 calls (profile + recent solves) karta aur logs persist karta  -  cron/manual sync pe chalta. Split isliye ki user-facing link kabhi timeout pe fail na ho.

**Q3: `defer_meta=True` kya karta hai aur kyun?**
A: Naye problem ke liye full metadata fetch (1 API call per problem) skip karke ek placeholder row (`difficulty=""`) banata. Isse sync hamesha 2 calls mein bounded rehta, chaahe 50 solves ho. Metadata baad mein nightly backfill cron/command `difficulty=""` rows ko bharta. Yeh Render timeout-driven design hai.

**Q4: GraphQL fail hone par bhi HTTP 200  -  isko code kaise handle karta?**
A: `query()` mein status 200 ke baad bhi `body.get("errors")` explicit check karta hai; non-empty `errors` array pe `LeetCodeAPIError` raise hota. Sirf status code dekhna kaafi nahi GraphQL ke liye.

**Q5: `tenacity` mein `reraise=True` kyun zaroori?**
A: Iske bina saare retries fail hone par tenacity apna `RetryError` wrap karke raise karta, jo `except LeetCodeAPIError` se miss ho jaata. `reraise=True` original `LeetCodeRateLimited` (jo `LeetCodeAPIError` ka subclass hai) ko re-raise karta, toh caller ka exception handling kaam karta.

**Q6: Cron endpoint JWT ke bajaye shared-secret kyun use karta?**
A: Cron ek external scheduler (GitHub Actions) hai, koi user session nahi. JWT user-specific hota aur expire hota  -  CI mein fragile. Shared secret (`X-Cron-Token` header, `secrets.compare_digest` se constant-time compared) simple aur stateless hai. `compare_digest` timing-attack se bachata.

**Q7: `SubmissionLog.problem` pe `on_delete=PROTECT` kyun, `CASCADE` kyun nahi?**
A: `Problem` ek shared catalog hai jo multiple users ke logs reference karte. CASCADE hota toh ek Problem delete hone par sab users ke woh solves silent delete ho jaate  -  data loss. PROTECT use mein hone wale Problem ko delete hone se rokta (safety net).

**Q8: `get_or_create` vs `update_or_create`  -  sync mein kaha kya use hua aur kyun?**
A: `SubmissionLog` pe `get_or_create`  -  agar same solve already hai toh kuch mat karo (idempotent dedup, `created` flag se naye count). `Problem` pe `update_or_create`  -  placeholder row ko fresh metadata se overwrite karna hai. Dono ke lookup fields pe unique constraint hai, isliye race-safe.

**Q9: `transaction.atomic()` `sync_account` mein kyun, aur network calls usse bahar kyun?**
A: 50 logs + account update ka all-or-nothing chahiye  -  beech mein fail hone par partial-write/inconsistent state na bane (rollback). Network calls bahar isliye ki slow I/O transaction ke andar DB connection/lock ko lambe time hold karta  -  transaction short rakhna performance rule hai.

---

#### Khud Try Kar (exercises)

1. **Naya transient error add karo.** Maan lo LeetCode kabhi-kabhi `502` ke saath ek "retry-able" body deta. `query()` mein 502 ko `LeetCodeRateLimited` mein map karo (taaki retry ho), phir `tests/test_services.py` mein `responses` se ek test likho jo verify kare ki 502 par exactly 3 attempts hue. (Hint: `retry.statistics` ya mock call-count check karo.)

2. **Stale-account guard banao.** Ek nayi field `last_attempt_at` ya logic add karo taaki `CronSyncAllView` un accounts ko skip kare jinka `sync_status == FAILED` hai aur jo pichle 1 ghante mein fail hue  -  taaki ek dead handle har cron run mein wastefully retry na ho. `sync.py` mein helper likho aur view ka query adjust karo.

3. **Backfill ko idempotent + observable banao.** `backfill_problems` command mein ek `--dry-run` flag add karo jo sirf print kare kitne `difficulty=""` rows pending hain (bina API call/DB write ke). Phir socho: agar `fetch_problem_meta` ek slug pe `LeetCodeUserNotFound`-type permanent error de (problem hi exist nahi karta), toh woh row hamesha `difficulty=""` mein atki rahegi aur har run mein retry hogi  -  is "poison row" problem ko kaise solve karoge? (Hint: ek `backfill_failed` sentinel ya attempt-counter.)

---

Relevant files (sab absolute paths):
- `d:\Grindmate\backend\apps\leetcode\services.py`  -  API client, DTOs, exception hierarchy, retry
- `d:\Grindmate\backend\apps\leetcode\sync.py`  -  orchestration, `verify_account`/`sync_account`, `defer_meta`, transactions
- `d:\Grindmate\backend\apps\leetcode\views.py`  -  HTTP layer, cron shared-secret endpoints
- `d:\Grindmate\backend\apps\leetcode\models.py`  -  schema, PROTECT, indexes, UniqueConstraint
- `d:\Grindmate\backend\apps\leetcode\serializers.py`  -  validation, read-only fields
- `d:\Grindmate\backend\apps\leetcode\managers.py`  -  reusable querysets (streak/this-week)
- `d:\Grindmate\backend\apps\leetcode\management\commands\sync_leetcode.py`  -  `--user/--handle/--all` command
- `d:\Grindmate\backend\apps\leetcode\management\commands\backfill_problems.py`  -  `--limit/--slug/--sleep` backfill
- `d:\Grindmate\backend\grindmate\settings\base.py:224,227`  -  `CRON_SHARED_SECRET`, `LEETCODE_GRAPHQL_URL`


---


## 5. Groups App + Leaderboard  -  Django ORM Masterclass

Dekh bhai, ye chapter sabse important hai. Backend interviews mein jo log "Django aata hai" bolte hain unmein se 90% sirf `Model.objects.filter()` aur `.all()` tak hi atke rehte hain. Asli ORM ki gehrai tab dikhti hai jab tu ek hi SQL query mein pura leaderboard nikaal de  -  counts, difficulty-weighted score, sorting  -  sab kuch DB pe compute hoke, Python loop ke bina. GrindMate ka leaderboard exactly yahi karta hai. Chal, ek-ek cheez kholte hain.

Pehle base samajh le: hamare paas teen models ka chain hai jisko ye query traverse karti hai:

```
Group --(M2M through GroupMembership)-- User --(reverse FK "submissions")-- SubmissionLog --(FK)-- Problem
```

`Problem.difficulty` field pe `"easy"/"medium"/"hard"` choices hain. `SubmissionLog.solved_at` pe time window lagta hai. Ye relationship map dimaag mein fix kar le  -  pura chapter isi par chalega.

---

#### 1. ManyToMany `through` model  -  metadata wali dosti

Normal M2M mein Django khud ek hidden join-table bana deta hai jismein sirf do FK hote hain (`group_id`, `user_id`). Lekin hamein membership pe extra info chahiye thi  -  banda **admin** hai ya **member**, aur **kab join** kiya. Bas isiliye `through` use kiya:

```python
# apps/groups/models.py
class Group(models.Model):
 members = models.ManyToManyField(
 settings.AUTH_USER_MODEL,
 through="GroupMembership",
 related_name="grindmate_groups",
 )
```

```python
class GroupMembership(models.Model):
 group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
 user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
 role = models.CharField(max_length=8, choices=ROLE_CHOICES, default=ROLE_MEMBER)
 joined_at = models.DateTimeField(auto_now_add=True)

 class Meta:
 constraints = [
 models.UniqueConstraint(fields=["group", "user"], name="unique_group_user"),
 ]
 indexes = [models.Index(fields=["user", "group"])]
```

**Kya hai:** `through="GroupMembership"` Django ko bolta hai  -  "auto join-table mat bana, main apna khud ka model de raha hoon jiske paas extra columns hain." Ye string isliye di (class object nahi) kyunki `GroupMembership` abhi neeche define hua hai  -  agar class object dete to NameError aata. Django strings ko lazily resolve karta hai migration/app-loading time pe.

**Kyun use kiya  -  design reasoning:** Plain M2M ka join-table dumb hota hai, sirf linkage. Jaise hi tujhe "is user ka is group mein role kya hai" ya "kab join kiya" jaisi koi cheez chahiye, plain M2M kaam nahi karta  -  tujhe ya to extra table chahiye ya `through`. `through` cleanest hai kyunki ORM ko pata rehta hai ye relationship table hai, aur tu `group.members.all()` (just users) bhi kar sakta hai aur `group.memberships.all()` (full membership rows with role) bhi.

**`related_name` ka khel  -  ye crucial hai:**
- `Group.members` ka `related_name="grindmate_groups"` → ek `user` se `user.grindmate_groups.all()` karke uske saare groups (as Group objects) mil jaate hain.
- Lekin `GroupMembership.group` ka `related_name="memberships"` → `group.memberships.all()` se membership **rows** milti hain (role/joined_at ke saath).
- `GroupMembership.user` ka bhi `related_name="memberships"` → `user.memberships.all()` se us user ki saari memberships.

Notice kar  -  leaderboard query `group.members` se shuru **nahi** hoti, `group.memberships` se shuru hoti hai:

```python
members_qs = group.memberships.select_related("user").annotate(...)
```

Kyun? Kyunki hamein membership row chahiye (taaki rank/role attach ho sake) aur `user` ko `select_related` se ek JOIN mein khींch sakein. Agar `group.members` se chalte to seedha User queryset milta aur membership metadata khona padta.

**UniqueConstraint(group, user):** Ye DB-level guarantee hai ki ek banda ek group mein do baar member nahi ban sakta. Ye sirf Python validation nahi  -  actual database mein `UNIQUE` constraint banta hai. Isiliye `JoinByInviteView` mein `get_or_create` race-safe ban paata hai (neeche dekhenge). Agar do parallel requests aayi to DB hi ek ko duplicate-key error de dega.

**`has_member` / `is_admin` helpers:**
```python
def has_member(self, user) -> bool:
 return self.memberships.filter(user=user).exists()

def is_admin(self, user) -> bool:
 return self.memberships.filter(user=user, role=GroupMembership.ROLE_ADMIN).exists()
```
`.exists()` important hai  -  ye `SELECT 1 ... LIMIT 1` fire karta hai, poori rows nahi khींchta. Sirf membership hai ya nahi, ye check karna ho to `.exists()` se fast aur memory-light hota hai.

---

#### 2. GroupInvite  -  token, auto-expiry, aur F() expression ka jaadu

```python
class GroupInvite(models.Model):
 DEFAULT_EXPIRY_HOURS = 24 * 7  # 7 days

 token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
 expires_at = models.DateTimeField()
 max_uses = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
 use_count = models.PositiveIntegerField(default=0)
 revoked = models.BooleanField(default=False)
```

**`default=secrets.token_urlsafe`:** Yahan `secrets.token_urlsafe` ko **call nahi** kiya (`token_urlsafe()` nahi likha)  -  sirf function reference diya. Django har nayi row pe khud isko call karta hai, taaki har invite ka token alag ho. Agar `token_urlsafe()` likh dete (with parentheses) to module load hote hi ek baar call hota aur **saare** invites ko same token milta  -  classic mutable-default-jaisa gotcha. `secrets` module cryptographically secure random deta hai (`random` module se safe  -  `random` predictable hai, invite tokens guess kiye ja sakte the).

**`save()` auto-expiry:**
```python
def save(self, *args, **kwargs):
 if not self.expires_at:
 self.expires_at = timezone.now() + timedelta(hours=self.DEFAULT_EXPIRY_HOURS)
 super().save(*args, **kwargs)
```
`expires_at` field pe koi `default` nahi diya, isliye `save()` override karke yahan set kiya. Kyun `default` field-level nahi diya? Kyunki field default static hota  -  agar `default=timezone.now() + timedelta(...)` likhte to wo bhi load-time pe ek baar evaluate hota (same wahi galti). `save()` mein karne se har naye invite par fresh "now + 7 days" milta hai. `super().save()` zaroor call kiya warna actual DB write hi nahi hota.

**`is_active()`:** Teen conditions  -  revoked nahi, expire nahi hua, aur max_uses cross nahi kiya. Note `max_uses is not None` check  -  `None` ka matlab unlimited uses.

**`consume()`  -  yeh interview gold hai:**
```python
def consume(self) -> None:
 self.use_count = models.F("use_count") + 1
 self.save(update_fields=["use_count"])
 self.refresh_from_db(fields=["use_count"])
```

**F() expression kya hai  -  under the hood:** Normal mein agar tu likhta:
```python
invite.use_count += 1 # read-modify-write
invite.save()
```
to ye teen steps mein hota: (1) Python ne pehle DB se padhi hui value `use_count` memory mein li, (2) usme +1 kiya, (3) wapas likh di. Beech mein agar **doosri request** bhi yahi kar rahi hai, to dono ne same purani value (maan le 5) padhi, dono ne 6 banaya, dono ne 6 likha  -  ek increment **kho** gaya. Ye **race condition** hai (lost update).

`models.F("use_count") + 1` Python mein add nahi karta. Ye ORM ko bolta hai SQL generate kar:
```sql
UPDATE group_invite SET use_count = use_count + 1 WHERE id = ...;
```
Ab increment **database engine** ke andar atomic hota hai  -  DB row-level locking se guarantee karta hai ki do parallel `+1` dono count honge. Koi read-modify-write Python side pe hai hi nahi, isliye lost-update impossible.

Ek catch: `F()` ke baad `self.use_count` ab ek `F` expression object hai, actual number nahi. Agar tu turant `invite.use_count` padhega to tujhe number nahi, expression milega. Isiliye `refresh_from_db(fields=["use_count"])` se DB se fresh actual value wapas memory mein laaya. `update_fields=["use_count"]` ne UPDATE ko sirf us ek column tak limit kiya  -  baaki fields ko touch nahi kiya (efficient + race-safe, kyunki tu galti se purani in-memory `revoked`/`expires_at` value overwrite nahi kar raha).

---

#### 3. `select_for_update` + `transaction.atomic`  -  invite join ki race ko maarna

```python
# apps/groups/views.py  -  JoinByInviteView
@transaction.atomic
def post(self, request, invite_token):
 invite = (
 GroupInvite.objects.select_related("group")
 .select_for_update()
 .get(token=invite_token)
 )
 ...
 membership, created = GroupMembership.objects.get_or_create(
 group=invite.group, user=request.user,
 defaults={"role": GroupMembership.ROLE_MEMBER},
 )
 if created:
 invite.consume()
```

Socho scenario: ek invite `max_uses=1` ka hai, aur do log **exactly same time** pe join button daba dete hain. Bina lock ke, dono ki `is_active()` check `True` return kar deti (kyunki dono ne `use_count=0` dekha), dono join ho jaate, max_uses=1 ka rule toot jaata.

**`select_for_update()` kya karta  -  under the hood:** Ye SQL mein `SELECT ... FOR UPDATE` generate karta hai. Jaise hi pehli transaction wo invite row padhti hai, DB us row pe **exclusive lock** laga deta hai. Doosri parallel transaction jab same row `SELECT ... FOR UPDATE` karne aayegi, to wo **block** ho jaayegi (wait karegi) jab tak pehli transaction commit/rollback nahi ho jaati. Pehli wali `consume()` karke `use_count=1` kar deti hai aur commit ho jaati hai. Tab doosri ko lock milta hai, wo fresh `use_count=1` padhti hai, `is_active()` ab `False` deta hai, aur usse "expired or fully used" 410 mil jaata hai. Race khatam.

**`transaction.atomic` zaroori hai kyun:** `select_for_update()` ka lock sirf transaction ke andar valid hota hai. Lock transaction commit hone tak hold rehta hai. Bina `atomic` ke, autocommit mode mein lock turant chhoot jaata aur poora point hi bekaar ho jaata  -  isiliye Django `select_for_update()` ko bina active transaction ke use karne pe error bhi deta hai. `@transaction.atomic` decorator poore `post` ko ek transaction mein wrap karta hai: ya to sab (membership create + consume) ek saath commit hoga, ya kuch fail hua to sab rollback. Atomicity = all-or-nothing.

Aur double protection bhi hai  -  `get_or_create` + DB ka `UniqueConstraint(group, user)`. Lock se invite count safe hai, unique constraint se duplicate membership safe hai.

---

#### 4. THE LEADERBOARD QUERY  -  line by line, har piece

Ab aate hain crown jewel pe. `apps/groups/leaderboard.py` ka `_compute_uncached`. Main isse tukdo mein todunga.

##### 4a. Period window  -  daily / weekly / all-time

```python
def _period_window(period):
 now = timezone.localtime()
 if period == "daily":
 start = now.replace(hour=0, minute=0, second=0, microsecond=0)
 return start, start + timedelta(days=1)
 if period == "weekly":
 start = now - timedelta(days=now.weekday()) # back to Monday
 start = start.replace(hour=0, minute=0, second=0, microsecond=0)
 return start, start + timedelta(days=7)
 return None, None # all-time
```

`timezone.localtime()`  -  aware datetime local TZ mein. `now.weekday()` Monday=0 deta, to `now - weekday days` se hafte ka Monday midnight nikalta. All-time pe `(None, None)` lautata  -  matlab koi window nahi.

##### 4b. Scope `Q` object  -  ek filter, har jagah reuse

```python
if start is not None:
 scope = Q(
 user__submissions__solved_at__gte=start,
 user__submissions__solved_at__lt=end,
 )
else:
 scope = Q()
```

**`Q` object kya hai:** `Q` ek "encapsulated condition" hai jise tu variable mein store karke, combine (`&`, `|`), negate (`~`) kar sakta hai. Yahan period ka time-window ek `Q` mein band kiya taaki har annotation mein dohra na padhe. All-time ke liye **khaali `Q()`**  -  ye "no filter, sab match" jaisa neutral element hai (jaise multiplication mein 1). Khaali `Q()` ko `&` se jodo to kuch effect nahi padta, isliye saari annotations same code path use kar paati hain  -  agar window hai to filter, nahi to sab.

**Relational lookup ka path:** Dhyaan de `user__submissions__solved_at`. Ye queryset `group.memberships` pe chal raha hai, to base model `GroupMembership` hai. Wahaan se:
- `user` → membership ka FK to User
- `submissions` → User ka reverse FK from SubmissionLog (`related_name="submissions"`)
- `solved_at` → SubmissionLog ka field

Double-underscore `__` ORM ka relationship-traversal operator hai. Ye SQL JOINs mein translate hota hai.

##### 4c. The annotated queryset  -  counts

```python
members_qs = (
 group.memberships.select_related("user")
 .annotate(
 total=Coalesce(Count("user__submissions", filter=scope, distinct=True), Value(0)),
 easy=Coalesce(
 Count(
 "user__submissions",
 filter=scope & Q(user__submissions__problem__difficulty="easy"),
 distinct=True,
 ),
 Value(0),
 ),
 # medium, hard same pattern...
```

Tukdo mein:

**`Count("user__submissions", ...)`  -  conditional/filtered aggregation:** Har membership row ke liye, us user ki submissions ginta hai. `Count` ek aggregate function hai jo SQL mein `COUNT(...)` banta. `.annotate()` ke andar hone se ye **per-row** aggregate hai (GROUP BY membership)  -  har banda apna alag count paata, ek global total nahi.

**`filter=scope`  -  yeh conditional aggregation ka asli magic hai:** Ye Django ka `FILTER` clause use karta  -  modern SQL mein `COUNT(...) FILTER (WHERE solved_at >= start AND solved_at < end)`. Matlab JOIN to saari submissions pe hua, lekin gina sirf wahi jo window mein aati hain. Ye `WHERE` se behtar hai kyunki agar tu top-level `WHERE` lagata to jis member ki **zero** submissions hain wo row hi gir jaati  -  leaderboard se gayab ho jaata. `FILTER` se row rehti hai, count 0 aata.

**`distinct=True`  -  kyun zaroori, deep:** Yeh sabse subtle gotcha hai. Ek hi query mein hum `user__submissions` (ek-se-many) ko join kar rahe hain aur saath mein `problem__difficulty` (submission ka FK) bhi. Jab tu ek query mein **multiple** joins karta hai jinme se koi one-to-many ho, to SQL rows ka **cross/cartesian multiplication** ho jaata. Iss se bina `distinct` ke `Count` over-count kar deta  -  same submission baar-baar gin jaati. `distinct=True` → `COUNT(DISTINCT submission.id)` banata, jisse har submission ek hi baar ginती hai chahe join kitna bhi fan-out kare. **Classic interview trap:** "ek annotate mein do alag aggregates daalo to counts double kyun ho jaate hain?" Jawaab  -  JOIN multiplication, fix `distinct=True`.

**`Coalesce(..., Value(0))`  -  NULL ko 0 banana:** SQL mein `COUNT` to 0 deta, par jab kuch match nahi hota / `Sum` mein koi row nahi aati, to aggregate `NULL` lautata hai. `Coalesce(x, Value(0))` SQL ka `COALESCE(x, 0)` hai  -  pehla non-NULL argument deta. Iska matlab Python side pe kabhi `None` nahi aayega, hamesha integer. `Value(0)` literal `0` ko ORM expression banata  -  bare `0` nahi de sakte kyunki Coalesce ko expression chahiye, raw Python int nahi (ye type-safety + SQL-literal escaping ke liye).

##### 4d. Difficulty-weighted score  -  Case/When/Sum

```python
score=Coalesce(
 Sum(
 Case(
 When(user__submissions__problem__difficulty="easy", then=Value(EASY_WEIGHT)), # 1
 When(user__submissions__problem__difficulty="medium", then=Value(MEDIUM_WEIGHT)),  # 3
 When(user__submissions__problem__difficulty="hard", then=Value(HARD_WEIGHT)), # 5
 default=Value(0),
 output_field=IntegerField(),
 ),
 filter=scope,
 ),
 Value(0),
),
```

**`Case`/`When` kya hai:** SQL ka `CASE WHEN ... THEN ... END`. Ye row-level conditional value deta. Har submission ke liye uske problem ki difficulty dekho, aur uske hisaab se ek number do  -  easy=1, medium=3, hard=5, na pata ho to 0.

**`Sum(Case(...))`:** Ab har submission ne ek number banaya, `Sum` un sabko jodke us user ka total weighted score deta. To ek hard + ek medium = 5 + 3 = 8. **Pure SQL** mein: `SUM(CASE WHEN difficulty='easy' THEN 1 WHEN ... END)`. Python ne ek bhi number add nahi kiya.

**`output_field=IntegerField()`:** Jab `Case`/`When` mein values mix ho sakti hain ya ORM khud type infer nahi kar paata, to wo confuse ho jaata aur error deta ("mixed types / cannot resolve expression type"). Yahan explicitly bola  -  result integer hai. Best practice: jab bhi `Case`/`Coalesce`/arithmetic mein type ambiguous ho, `output_field` de do.

**`filter=scope` yahan bhi:** Score bhi sirf period-window ki submissions pe. Weekly leaderboard pe sirf is hafte ka score.

##### 4e. Ordering

```python
.order_by("-score", "-total", "user__username")
```
Pehle highest score upar (`-` = descending), tie ho to zyada total solves wala, fir tie ho to username alphabetical (stable, deterministic). Deterministic ordering important hai  -  bina last tie-breaker ke same-score wale random order mein aa sakte the (aur pagination / cache mein flicker hota).

##### 4f. SABSE BADA POINT  -  ye sab ONE SQL query hai

Pura `members_qs`  -  N members, har ek ke 5 alag aggregates (total/easy/medium/hard/score)  -  ye sab **ek hi `SELECT`** mein DB pe compute hota hai. Python sirf taiyaar (already-computed) numbers receive karta. Agar yahi Python mein karte:

```python
# BAD  -  kabhi mat karna
for m in group.memberships.all():
 subs = m.user.submissions.filter(solved_at__gte=start) # N queries
 m.total = subs.count()
 m.easy = subs.filter(problem__difficulty="easy").count()  # aur queries...
```
ye N×kai queries fire karta, aur ginti Python mein hoti  -  slow, memory-heavy, scale nahi karta. Annotated query push karti hai computation database ke paas, jahan indexes (`submission_user_date_idx`) ka faida milta. **Yahi line interview mein bolni hai:** "leaderboard ek single annotated query hai, saare per-member aggregates database FILTER/CASE clauses mein compute hote hain, Python sirf rows iterate karta."

> **Lazy evaluation note:** `members_qs` define karne pe DB pe kuch fire **nahi** hota  -  queryset lazy hai. SQL tab chalta hai jab pehli baar iterate hota: `user_ids = [m.user_id for m in members_qs]` wali line. Uske baad Django result ko cache kar leta, to neeche `enumerate(members_qs)` wali loop **dobara** query fire nahi karti  -  same evaluated result reuse hota.

---

#### 5. N+1 problem  -  `select_related` vs `prefetch_related`

**N+1 kya hota hai:** Tu ek query se N parent objects laata hai (1 query), fir loop mein har parent ka related object access karta hai  -  har access ek extra query (N queries). Total 1 + N. 50 members = 51 queries. Ye silent killer hai  -  code chalta hai theek, par DB pe load phat-ta hai.

```python
for m in group.memberships.all(): # 1 query
 print(m.user.username) # har baar +1 query → N queries
```

**`select_related` (FK / OneToOne  -  JOIN):** Forward single-valued relationships ke liye. SQL `JOIN` lagake related rows same query mein le aata. Hamare leaderboard mein:
```python
group.memberships.select_related("user")
```
Isse `m.user.username` access karne pe extra query nahi lagti  -  user already JOIN se aa chuka. Streak loop mein har row pe `m.user.public_id`, `m.user.username`, `m.user.avatar_url` access hota  -  `select_related` ke bina ye N+1 ban jaata.

**`prefetch_related` (M2M / reverse FK  -  separate query):** Multi-valued relationships ke liye JOIN se kaam nahi banta (multiplication). Iske bajaay Django ek **doosri** query fire karke related objects laata, fir Python mein match karke attach karta. Repo mein `GroupListCreateView`:
```python
.prefetch_related(
 Prefetch("memberships", queryset=GroupMembership.objects.filter(user=self.request.user)),
)
```
`Prefetch` object custom queryset deta  -  yahan saari memberships nahi, sirf current user ki membership prefetch karo. Iska use `GroupSerializer.get_role` mein hota:
```python
def get_role(self, obj):
 membership = next((m for m in obj.memberships.all() if m.user_id == request.user.id), None)
 return membership.role if membership else None
```
`obj.memberships.all()` already prefetch ho chuka, isliye list of groups mein har group ke role nikalne pe **ek bhi extra query nahi** lagti  -  N+1 mar gaya. Agar prefetch na hota to har group ke liye ek membership query, list endpoint mein N+1.

**`GroupDetailView`** mein `.prefetch_related("memberships__user")`  -  nested prefetch: memberships bhi, aur har membership ka user bhi. Detail page pe member list dikhane ke liye.

**Yaad rakhne ka rule:** ek (FK/O2O) → `select_related` (JOIN). Many (reverse FK / M2M) → `prefetch_related` (alag query).

---

#### 6. Streaks  -  SQL nahi, Python mein kyun

```python
# leaderboard.py
distinct_dates = (
 SubmissionLog.objects.filter(user_id__in=user_ids)
 .annotate(d=TruncDate("solved_at"))
 .values_list("user_id", "d")
 .distinct()
 .order_by("-d")
)
user_dates = {}
for user_id, d in distinct_dates:
 user_dates.setdefault(user_id, []).append(d)
```

**`TruncDate("solved_at")`:** Datetime ko date pe truncate (time part hata do). SQL mein date-cast banta. Kyun? Streak "din" pe based hai, second pe nahi  -  ek din mein 5 solve bhi ek hi "active day" hai.

**`values_list("user_id", "d").distinct()`:** Sirf 2 columns (user, date) tuples ke roop mein. `.distinct()` se per-user duplicate dates hat jaati. **Ek hi query** mein saare members ke saare distinct active-dates aa jaate (`user_id__in=user_ids`)  -  fir Python mein `user_dates` dict mein group kar diya. Ye N+1 ka classic fix hai: per-user alag query maarne ke bajaay ek `IN` query.

Ab actual streak algorithm  -  `apps/leetcode/managers.py` `compute_streaks`:

```python
def compute_streaks(distinct_dates):
 if not distinct_dates:
 return 0, 0
 today = timezone.localdate()
 sorted_desc = sorted(set(distinct_dates), reverse=True)

 # current streak  -  sirf tab count jab aaj ya kal solve kiya ho
 current = 0
 expected = today
 for d in sorted_desc:
 if d == expected:
 current += 1
 expected = expected - timedelta(days=1)
 elif d == expected - timedelta(days=1) and current == 0:
 current = 1
 expected = d - timedelta(days=1)
 else:
 break

 # longest streak  -  ascending scan
 sorted_asc = sorted(set(distinct_dates))
 longest = run = 1
 for prev, curr in pairwise(sorted_asc):
 if curr - prev == timedelta(days=1):
 run += 1
 longest = max(longest, run)
 else:
 run = 1
 return current, longest
```

**Current streak logic:** Aaj se peeche chalo. Agar latest date aaj hai → streak start, `expected` ko kal pe le jao. Phir har consecutive day ginte jao. `elif ... current == 0` wala edge case: agar aaj solve nahi kiya par kal kiya, to streak abhi "zinda" hai (kyunki aaj khatam nahi hua)  -  isliye kal se gينti shuru. Beech mein gap aaya → `break`.

**`itertools.pairwise`:** `pairwise([a,b,c])` → `(a,b),(b,c)`  -  consecutive pairs. Python 3.10+. Manually `range(len-1)` likhne se cleaner. Longest streak ke liye ascending dates pe consecutive pairs dekho  -  agar `curr - prev == 1 day` to run badhao, warna run reset. `longest` max track karta.

**Python mein kyun, SQL mein kyun nahi  -  design reasoning:** Ye "gaps and islands" problem hai. SQL mein consecutive-date streaks nikalna window functions (`ROW_NUMBER`, date minus row_number trick) se hota hai jo padhne/maintain karne mein bahut painful hai, aur SQLite/MySQL portability bhi tang karti. Distinct dates already DB se ek sasti query mein aa gayi (per user shायद 100-200 dates), to Python mein O(n) scan trivial hai. **Right tool for the job:** bulk aggregation DB pe (counts/score), date-sequence logic Python pe.

---

#### 7. Custom QuerySet + Manager  -  chainable power

```python
# apps/leetcode/managers.py
class SubmissionLogQuerySet(models.QuerySet):
 def for_user(self, user): return self.filter(user=user)
 def in_range(self, start, end): return self.filter(solved_at__gte=start, solved_at__lt=end)
 def today(self):  ...  return self.in_range(start, start + timedelta(days=1))
 def this_week(self): ... return self.in_range(start, start + timedelta(days=7))
 def by_difficulty(self): ... # {difficulty: count}

class SubmissionLogManager(models.Manager.from_queryset(SubmissionLogQuerySet)):
 def get_queryset(self):
 return SubmissionLogQuerySet(self.model, using=self._db)
```

Model pe: `objects = SubmissionLogManager()`.

**Chainable kyun powerful  -  under the hood:** Har custom method `self.filter(...)` karke **wapas ek queryset** lautata hai. Aur kyunki wo bhi `SubmissionLogQuerySet` hi hai, uspe dobara custom method chain ho sakti hai:
```python
SubmissionLog.objects.for_user(u).this_week().by_difficulty()
```
Ye padhne mein English jaisa hai aur har piece reusable. Agar ye sab views mein `filter(user=.., solved_at__gte=..)` likhte to har jagah dohraana padta aur ek jagah logic badla to sab jagah badalna padta. QuerySet mein encapsulate karne se **single source of truth** ban gaya  -  module docstring exactly yahi bolta: "views aur Celery tasks ko ORM noise se mukt rakhna."

**`Manager.from_queryset` ka jaadu:** Normally manager aur queryset alag hote  -  queryset ki methods manager pe nahi dikhti. Matlab `SubmissionLog.objects.for_user(u)` direct kaam nahi karta, pehle `.all()` ya `.get_queryset()` chahiye hota. `Manager.from_queryset(SubmissionLogQuerySet)` dynamically ek manager class banata jo queryset ki saari custom methods ko **manager pe bhi expose** kar deta. Isliye `SubmissionLog.objects.for_user(...)` (bina `.all()` ke) seedha chalta. Ye Django ki proper way hai DRY rakhne ki  -  chaining behaviour bhi milti, manager-level entry-point bhi.

**`by_difficulty` thoda alag:** Ye queryset nahi, **dict** lautata (`values(...).annotate(Count).values_list(...)` → `dict(...)`). Profile page pe `{"easy": 40, "medium": 12, ...}` chahiye, isliye terminal method hai  -  chain yahaan toot-ti hai (jaan-bujh ke, kyunki ye final shape hai).

---

#### 8. Caching + invalidation  -  speed bhi, freshness bhi

```python
LEADERBOARD_CACHE_TTL = 60  # seconds

def _cache_key(group_public_id, period):
 return f"leaderboard:{group_public_id}:{period}"

def compute_leaderboard(group, period="weekly"):
 key = _cache_key(str(group.public_id), period)
 hit = cache.get(key)
 if hit is not None:
 return hit
 rows = _compute_uncached(group, period)
 cache.set(key, rows, timeout=LEADERBOARD_CACHE_TTL)
 return rows
```

**Pattern (cache-aside / lazy caching):** Pehle cache dekho. Mila (`hit is not None`) → wahi lauta do, mehngi query skip. Nahi mila → compute karo, cache mein daalo TTL ke saath, lauta do. Leaderboard har request pe wahi heavy annotated query na chalaye  -  popular group ka leaderboard ek baar compute hoke 60 second cache hota.

**`hit is not None` kyun, `if hit:` kyun nahi:** Khaali leaderboard (`[]`) bhi valid cached result hai! `if hit:` empty list ko falsy maanke cache-miss samajh leta aur baar-baar recompute karta. `is not None` se "key cache mein hai hi nahi" aur "key hai par value empty list" ko alag-alag handle kiya. **Sookshm par important gotcha.**

**Key design:** `leaderboard:<group_public_id>:<period>`  -  group-aware aur period-aware. Daily/weekly/all-time ke alag cache entries, taaki ek period ka data doosre ko pollute na kare. `public_id` (UUID) use kiya internal `id` ke bajaay  -  keys guess/enumerate karna mushkil.

**Invalidation  -  sabse hard part of caching:** "There are only two hard things in CS: cache invalidation and naming things." Stale leaderboard mat dikhao  -  jaise hi koi member solve kare, uske saare groups ka leaderboard cache drop karo:

```python
# leaderboard.py
def invalidate_group_leaderboard(group_public_id):
 for period in ("daily", "weekly", "all-time"):
 cache.delete(_cache_key(group_public_id, period))
```

```python
# apps/leetcode/signals.py
@receiver(post_save, sender=SubmissionLog)
def invalidate_leaderboards_on_solve(sender, instance, created, **kwargs):
 if not created:
 return
 group_ids = list(instance.user.memberships.values_list("group__public_id", flat=True))
 for public_id in group_ids:
 invalidate_group_leaderboard(str(public_id))
```

**Signal kaise kaam karta:** `post_save` signal `SubmissionLog` save hone ke baad fire hota. `@receiver` decorator is function ko us signal se bind karta. `created` flag batata ki nayi row bani (True) ya existing update hui (False).

**`if not created: return`  -  kyun crucial:** Sirf **naye** solve pe cache drop karna hai. Agar koi existing row update hui (e.g. backfill), to leaderboard count nahi badla  -  bekaar mein cache nahi girana. Ye unnecessary recompute bachata.

**Invalidation strategy (delete, not update):** Cache ko naya value se update nahi karte  -  bas **delete** karte hain. Agla read miss hoga aur fresh compute karke wapas bhar dega. Ye simple aur sahi hai  -  ye sochna nahi padta ki "naya solve se exact naya leaderboard kya hoga" (jo phir wahi query chalani padti). Bas drop karo, agla reader recompute karega.

**Do-layer protection:** TTL=60s ek **safety net** hai. Maan le signal kisi edge case (bulk insert jo `post_save` skip karta, ya cache backend hiccup) mein miss ho gaya  -  to bhi 60s baad TTL expire hone se data refresh ho jaayega. Signal = immediate freshness, TTL = eventual consistency backstop. Dono milke robust.

> **Gotcha:** `SubmissionLog.objects.bulk_create()` `post_save` signal **fire nahi** karta. Agar sync code bulk_create use kare to leaderboard stale reh sakta  -  TTL save karta hai, par agar instant freshness chahiye to bulk insert ke baad `invalidate_group_leaderboard` manually call karna padega. Interview mein ye bolna seniority dikhata.

---

#### 9. Serializers  -  dataclass se JSON tak

**`GroupSerializer.get_role`  -  `SerializerMethodField`:**
```python
role = serializers.SerializerMethodField()

def get_role(self, obj):
 request = self.context.get("request")
 if request is None or not request.user.is_authenticated:
 return None
 membership = next((m for m in obj.memberships.all() if m.user_id == request.user.id), None)
 return membership.role if membership else None
```
`SerializerMethodField` un fields ke liye hai jo model pe seedha exist nahi karte  -  yahan "current user ka is group mein role". Naming convention strict: field `role` → method `get_role` (Django apne aap dhूंdh leta). `self.context` se request milta (view automatically context mein request daalta). Notice  -  `obj.memberships.all()` pe Python `next()` use kiya, naya DB query nahi maara, kyunki view ne already `prefetch_related` kiya tha. Agar yahan `.filter(user=..)` likh dete to har row pe N+1 ban jaata  -  prefetch ka faida khatam.

**Nested `GroupMembershipSerializer`:**
```python
class GroupMembershipSerializer(serializers.ModelSerializer):
 user = UserSerializer(read_only=True)
 class Meta:
 model = GroupMembership
 fields = ("user", "role", "joined_at")
```
Nested serializer  -  membership ke andar pura user object (UserSerializer se) embed hota. `read_only=True` kyunki member list sirf padhne ke liye, write nahi.

**`LeaderboardRowSerializer`  -  dataclass mirror:**
```python
class LeaderboardRowSerializer(serializers.Serializer):
 rank = serializers.IntegerField()
 public_id = serializers.CharField()
 # ... LeaderboardRow ke fields exactly mirror
```
Ye `ModelSerializer` **nahi**, plain `Serializer` hai  -  kyunki source model nahi, ek **dataclass** (`LeaderboardRow`) hai. View mein:
```python
data = LeaderboardRowSerializer([asdict(r) for r in rows], many=True).data
```
`asdict(r)` dataclass ko dict banata, `many=True` list ke liye. **Design reasoning:** leaderboard rows DB model nahi (computed/annotated hain), to frozen dataclass use kiya  -  type-safe, immutable, IDE autocomplete deta. Serializer uska shape JSON ke liye validate/format karta. Dataclass aur serializer fields ko sync rakhna padta (mirror)  -  ye conscious tradeoff hai clarity ke liye.

---

#### 10. Object-level permissions

```python
# apps/groups/permissions.py
class IsGroupMember(permissions.BasePermission):
 message = "You are not a member of this group."
 def has_object_permission(self, request, view, obj):
 return obj.has_member(request.user)

class IsGroupAdmin(permissions.BasePermission):
 message = "Admin permission required for this group."
 def has_object_permission(self, request, view, obj):
 return obj.owner_id == request.user.id or obj.is_admin(request.user)
```

**Do level ki permission:** DRF mein `has_permission` (view-level  -  "endpoint access kar sakta ya nahi") aur `has_object_permission` (object-level  -  "is specific group pe action kar sakta ya nahi"). Member-check object-level hai kyunki har group alag hai.

**`check_object_permissions`  -  manually kyun:** `GenericAPIView` ke `get_object()` mein DRF khud `has_object_permission` call karta. Lekin jab tu plain `APIView` use karta (`LeaderboardView`, `GroupInviteView`, `JoinByInviteView`) ya manually `get_object_or_404` karta, to DRF ko pata nahi obj kaunsa hai  -  isliye **khud** call karna padta:
```python
group = get_object_or_404(Group, public_id=public_id)
self.check_object_permissions(request, group) # ye loop chalata har permission ka has_object_permission
```
`check_object_permissions` saari permission classes ka `has_object_permission` chalata; koi `False` de to `PermissionDenied` (403) raise, `message` ke saath. Bhulna common bug hai  -  tab object fetch to hota par permission check skip ho jaata (security hole).

**`get_permissions()` per-method:**
```python
# GroupDetailView
def get_permissions(self):
 if self.request.method in permissions.SAFE_METHODS: # GET/HEAD/OPTIONS
 return [permissions.IsAuthenticated(), IsGroupMember()]
 return [permissions.IsAuthenticated(), IsGroupAdmin()]
```
Static `permission_classes` ke bajaay `get_permissions()` runtime pe HTTP method dekhke alag permissions deta  -  **read** ke liye member kaafi, **write/delete** (PATCH/DELETE) ke liye admin chahiye. `SAFE_METHODS` = GET/HEAD/OPTIONS (read-only). Notice  -  yahan permissions **instances** return hote (`IsGroupMember()` with parens), jabki static `permission_classes` mein classes (bina parens). Ye DRF ka contract hai aur galti karna easy.

---

#### Common Galtiyan / Gotchas (consolidated)

| Galti | Kya hota | Fix |
|---|---|---|
| Multiple aggregates bina `distinct=True` | JOIN multiplication se counts double/triple | `Count(..., distinct=True)` |
| `if hit:` cache check | Empty `[]` ko miss samajhke recompute | `if hit is not None:` |
| `default=secrets.token_urlsafe()` (parens) | Saare rows ko same token | reference do, call mat karo |
| `obj.use_count += 1` parallel writes | Lost update race | `F("use_count") + 1` |
| `select_for_update` bina `transaction.atomic` | Lock turant chhoot jaata / error | `@transaction.atomic` wrap |
| Plain `APIView` mein object perm bhoolna | Security hole, koi bhi access | `self.check_object_permissions(...)` |
| Serializer mein `.filter()` per row | N+1 despite prefetch | prefetched data pe Python `next()`/loop |
| `output_field` na dena Case/Coalesce mein | "mixed types" error | explicit `output_field=IntegerField()` |
| `bulk_create` se cache invalidation expect karna | `post_save` fire nahi hota, stale data | manual invalidate ya TTL pe rely |

---

#### Interview Questions + Short Answers

**Q1: M2M mein `through` model kab aur kyun use karte ho?**
Jab relationship pe extra metadata chahiye (yahan `role`, `joined_at`). Plain M2M ka auto join-table sirf 2 FK rakhta; `through` se custom columns add hote, aur ORM phir bhi relationship-aware rehta.

**Q2: `F()` expression kya solve karta hai?**
Read-modify-write race (lost update). `F("use_count")+1` Python mein add nahi karta, SQL `SET use_count = use_count + 1` generate karta  -  increment DB ke andar atomic, parallel-safe.

**Q3: Leaderboard query mein `distinct=True` kyun chahiye?**
Ek query mein submissions (one-to-many) + problem (FK) dono join hote → SQL rows multiply. `distinct=True` → `COUNT(DISTINCT id)`, har submission ek hi baar gini jaati, over-count rukता.

**Q4: `filter=scope` (conditional aggregation) `WHERE` se behtar kyun?**
`WHERE` top-level se zero-submission member ki row hi gir jaati  -  leaderboard se gayab. `FILTER` clause se row rehti hai, sirf matching submissions ginti hain, baaki ko count 0 milta.

**Q5: `select_related` vs `prefetch_related`?**
`select_related`  -  FK/OneToOne, SQL JOIN, ek query, single-valued. `prefetch_related`  -  M2M/reverse-FK, alag query + Python join, multi-valued. Dono N+1 maarte, applicability alag.

**Q6: Streak SQL mein kyun nahi nikala?**
Consecutive-date streak "gaps and islands" hai  -  SQL window-function trick padhne/maintain karne mein painful aur DB-portability todta. Distinct dates ek sasti query se aa jaati, Python O(n) scan se streak nikalna saaf aur simple.

**Q7: Cache invalidation kaise handle kiya?**
`post_save` signal (only `created`) member ke saare groups ka cache `delete` karta (update nahi). Plus 60s TTL safety-net. Immediate freshness + eventual-consistency backstop.

**Q8: `check_object_permissions` manually kab call karna padta?**
Jab plain `APIView` ya manual `get_object_or_404` use karo  -  DRF auto sirf `GenericAPIView.get_object()` mein call karta. Na karo to object-level perm skip = security hole.

**Q9: `Manager.from_queryset` kya deta hai?**
QuerySet ki custom methods ko Manager pe expose karta, taaki `Model.objects.for_user(u)` bina `.all()` ke chale, aur chainability bhi bani rahe. DRY entry-point.

---

#### Khud Try Kar (Exercises)

**1. SQL khud dekho:** Django shell mein  - 
```python
from apps.groups.leaderboard import _compute_uncached
qs = ...  # members_qs ko isolate karke
print(str(qs.query))
```
ya `qs.explain()` chalake dekho `COUNT(DISTINCT ...) FILTER (WHERE ...)` aur `CASE WHEN` generate ho raha hai ki nahi. Try: `distinct=True` hata ke counts kaise badalte dekho.

**2. N+1 pakdo:** `django-debug-toolbar` ya `connection.queries` se `GroupListCreateView` ki query-count gino. Fir `prefetch_related(Prefetch("memberships", ...))` line comment karke dobaara gino  -  N+1 explosion live dekho.

**3. Naya period add karo:** "monthly" leaderboard add kar  -  `_period_window` mein month-start logic, `invalidate_group_leaderboard` ke tuple mein `"monthly"` add, view ke validation set mein bhi. Dekh kितni jagah touch karni padti (cohesion/coupling ka feel aayega), aur cache key naturally `leaderboard:<id>:monthly` ban jaayegi.


---


## 6. Celery, Migrations, Caching & Testing (Supporting Cast)

Ab tak humne API, serializers, ORM dekhe  -  yeh sab ek HTTP request ke andar synchronously chalta hai. Lekin har kaam request ke andar nahi ho sakta. LeetCode se data pull karna slow hai (network call, rate limits), aur user ko 30 second tak loader dikhana acceptable nahi. Isiliye GrindMate mein ek poora "infrastructure layer" hai  -  background jobs (Celery), schema evolution (migrations), caching, aur ek tezz test suite jo bina kisi external service ke chalta hai.

Is chapter mein hum yeh sab is repo ke real code se samjhenge.

---

#### 1. Celery  -  task queue ka poora concept

Pehle problem samajh. Maan le user ne apna LeetCode handle link kiya. Ab tujhe LeetCode se uska profile + recent solves pull karne hai. Agar tu yeh sab HTTP request ke andar kare:

- LeetCode ka GraphQL endpoint slow + rate-limited hai
- agar 200 users ka sync ek saath karna ho, to ek hi request kabhi khatam nahi hogi
- user ka browser timeout ho jayega

Solution: **kaam ko ek queue mein daal do, aur ek alag process (worker) usko background mein chalaye.** Yahi Celery karta hai.

Celery ke 4 hisse hote hain  -  yeh terminology rat le, interviews mein poochte hain:

| Component | Kya hai | GrindMate mein |
|-----------|---------|----------------|
| **Task** | Ek Python function jo background mein chalega | `sync_account_task`, `sync_all_accounts` |
| **Broker** | Message queue jahan tasks store hote hain jab tak worker uthata nahi | Redis (`CELERY_BROKER_URL`) |
| **Worker** | Alag process jo broker se task uthata aur chalata hai | `celery -A grindmate worker` |
| **Beat** | Scheduler  -  fixed interval pe tasks ko queue mein push karta (cron jaisa) | `celery -A grindmate beat` |

Flow yeh hai: tu code mein `sync_account_task.delay(id)` likhta hai → Celery us call ko **serialize** karke (JSON) **broker (Redis)** mein daal deta hai → **worker** Redis se message uthata hai, deserialize karta hai, aur actual function chalata hai. Tera web process turant free ho jaata hai.

##### app banana  -  `celery.py`

`backend/grindmate/celery.py`:

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grindmate.settings.development")

app = Celery("grindmate")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

Line-by-line, under the hood kya ho raha hai:

- `os.environ.setdefault("DJANGO_SETTINGS_MODULE", ...)`  -  Celery worker ek **standalone process** hai, woh Django ke through start nahi hota. Isiliye usko khud batana padta hai ki Django settings kahan hain, warna `from .models import ...` crash karega ("Apps aren't loaded yet").
- `app.config_from_object("django.conf:settings", namespace="CELERY")`  -  yeh keh raha hai "Celery ki saari config Django settings se utha, lekin sirf woh keys jo `CELERY_` se shuru hoti hain." Yani settings mein `CELERY_BROKER_URL` → Celery ke andar `broker_url` ban jata hai. Namespace ka fayda: ek hi `settings.py` mein Django config aur Celery config dono rakh sakta hai bina naam takrane ke.
- `app.autodiscover_tasks()`  -  yeh `INSTALLED_APPS` mein har app ke andar `tasks.py` dhoondh ke usko import kar leta hai. Isiliye tu task ko alag se register nahi karta  -  bas `apps/leetcode/tasks.py` likh diya, Celery khud pakad lega.

Ab settings side, `backend/grindmate/settings/base.py`:

```python
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 5 * 60 # hard kill after 5 min
CELERY_TASK_SOFT_TIME_LIMIT = 4 * 60 # raise SoftTimeLimitExceeded at 4 min
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
```

Notice `CELERY_RESULT_BACKEND = "django-db"`  -  task ka return value Django ke database mein store hoga (via `django_celery_results` app). `CELERY_BEAT_SCHEDULER = "...DatabaseScheduler"`  -  beat ka schedule code mein hardcode nahi, **database mein** store hota hai (via `django_celery_beat`). Yeh point #4 mein bahut important banega.

`json` serializer kyun, `pickle` kyun nahi? Pickle se arbitrary Python objects bhej sakte the, lekin pickle ek **remote code execution** risk hai  -  agar koi broker compromise kar le to malicious pickle bhej ke server pe code chala sakta hai. JSON safe hai, isiliye task ko sirf JSON-serializable arguments (int, str, dict) pass karne chahiye  -  isiliye humne `sync_account_task` ko `account_id` (int) pass kiya, poora `account` object nahi.

##### Tasks  -  `@shared_task`, `bind=True`, retries

`backend/apps/leetcode/tasks.py`:

```python
@shared_task(
 name="leetcode.sync_account",
 bind=True,
 autoretry_for=(Exception,),
 retry_backoff=30,
 retry_jitter=True,
 max_retries=3,
)
def sync_account_task(self, account_id: int) -> dict:
 """Sync a single LeetCodeAccount by id."""
 try:
 account = LeetCodeAccount.objects.select_related("user").get(pk=account_id)
 except LeetCodeAccount.DoesNotExist:
 logger.info("LeetCodeAccount id=%s gone - skipping sync.", account_id)
 return {"skipped": True}
 ...
```

Har argument ka matlab:

- **`@shared_task`** vs `@app.task`  -  `shared_task` app instance se bandha nahi hota. Yeh isiliye use karte hain taaki app ki `tasks.py` ko `celery.py` import na karna pade (circular import bachta hai). `shared_task` "kisi bhi Celery app ke saath kaam karega" wala generic decorator hai.
- **`name="leetcode.sync_account"`**  -  explicit naam diya. Agar nahi dete to Celery `apps.leetcode.tasks.sync_account_task` jaisa auto-naam banata. Explicit naam isiliye chahiye kyunki migration (point #4) mein hum is naam ka string use karke task register karte hain  -  agar module path badla to schedule toot jaata. Stable name = stable contract.
- **`bind=True`**  -  isse function ka pehla argument `self` ban jaata hai (task instance). `self.request` se retry count, task id milta hai. Iske bina tu manual `self.retry()` nahi call kar sakta.
- **`autoretry_for=(Exception,)`**  -  agar task ke andar koi bhi `Exception` raise ho, Celery khud retry karega. Manual try/except/retry likhne ki zaroorat nahi.
- **`retry_backoff=30`**  -  pehla retry 30s baad, fir 60s, fir 120s (exponential). Iska reason: agar LeetCode rate-limit kar raha hai, turant retry karne se aur block hoga. Backoff "thoda saans le" wali strategy hai.
- **`retry_jitter=True`**  -  backoff time mein thoda random offset add karta hai. **Thundering herd** problem se bachata: agar 100 tasks ek saath fail hue, sab exactly 30s baad retry karenge → server pe spike. Jitter unhe time pe phaila deta.
- **`max_retries=3`**  -  3 baar fail hone ke baad give up.

Dhyaan de `DoesNotExist` ko humne try/except mein pakda aur `{"skipped": True}` return kiya  -  retry **nahi** kiya. Logic: agar account delete ho gaya, to retry karne ka koi point nahi (account wapas nahi aane wala). Retry sirf **transient** failures (network, rate-limit) ke liye useful hai, **permanent** failures ke liye nahi.

##### Fan-out pattern  -  `sync_all_accounts`

```python
@shared_task(name="leetcode.sync_all_accounts")
def sync_all_accounts() -> dict:
 pending = LeetCodeAccount.objects.exclude(sync_status=SyncStatus.UNVERIFIED)
 queued = 0
 for account_id in pending.values_list("id", flat=True):
 sync_account_task.delay(account_id)
 queued += 1
 return {"queued": queued}
```

Yeh **fan-out** pattern hai  -  ek "dispatcher" task jo kaam khud nahi karta, balki har account ke liye ek alag chhota task **queue** kar deta hai. Fayde:

1. **Parallelism**  -  multiple workers alag-alag accounts ek saath process kar sakte hain.
2. **Isolation**  -  agar ek account ka sync fail hua (uska LeetCode handle delete ho gaya), woh sirf uska apna task fail karega, baaki sab chalte rahenge. Ek monolithic loop hota to ek exception poora batch tod deta.
3. **Retry granularity**  -  sirf failed account retry hoga, sab nahi.

`.values_list("id", flat=True)` ka use isiliye  -  humein poore objects nahi chahiye, sirf id chahiye `.delay()` ke liye. Yeh DB se sirf ek column khींchta hai (memory + bandwidth bachta). `flat=True` se `[1, 2, 3]` milta hai bajaye `[(1,), (2,), (3,)]` ke.

`.delay(account_id)` = `.apply_async(args=[account_id])` ka shortcut  -  yeh task ko **abhi nahi chalata**, broker mein push karta hai aur turant return ho jaata hai.

---

#### 2. `CELERY_TASK_ALWAYS_EAGER`  -  dev/test mein synchronous

`backend/grindmate/settings/test.py`:

```python
# Run Celery tasks synchronously, no broker needed.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

`ALWAYS_EAGER = True` ka matlab: jab tu `.delay()` call kare, Celery broker mein push nahi karega  -  woh task ko **wahीं, usi process mein, synchronously** chala dega aur result return kar dega. Effectively `.delay(x)` ab ek normal function call ban jaata hai.

Yeh kyun chahiye? **Tests/dev mein Redis aur worker nahi chahiye.** Test suite ko fast aur self-contained rakhna hai. Agar `ALWAYS_EAGER` nahi hota:
- har test ke liye Redis chahiye hota
- `.delay()` call karke result kabhi nahi milta (kyunki worker hi nahi chal raha), assertions fail ho jaate

`EAGER_PROPAGATES = True` ek important sahyogi flag hai: eager mode mein agar task ke andar exception aaye, by default Celery usko swallow kar leta (jaise async mein hota  -  error result mein chala jaata). Yeh flag kehta hai "nahi, exception ko **upar throw kar** taaki test mein fail dikhe." Iske bina ek buggy task silently pass kar jaata test mein.

**Gotcha:** eager mode mein `autoretry_for` / `retry_backoff` ka behaviour production se alag ho sakta hai (retries synchronously aur turant ho jaate, jitter/backoff effectively skip). Isiliye GrindMate mein retry logic ka test alag hota hai  -  `test_services.py` mein `tenacity` retry directly test kiya gaya hai (point #8 mein dekhenge), Celery ke `autoretry` pe depend nahi kiya.

---

#### 3. Prod reality  -  Render free pe worker nahi, GitHub Actions cron

Yeh GrindMate ka sabse pyaara design decision hai. Theory mein humne Celery beat + worker setup kiya. **Lekin Render ke free tier pe ek hi web process milta hai  -  koi alag "worker dyno" nahi.** Matlab production mein na beat chal sakta, na worker.

To solution kya? **GitHub Actions ko hi Celery beat bana do.** GitHub Actions free mein scheduled (cron) workflows deta hai. Woh har 6 ghante ek HTTP endpoint hit karega, aur woh endpoint synchronously sync chala dega.

`backend/apps/leetcode/views.py` mein woh endpoint:

```python
class CronSyncAllView(APIView):
 """POST /api/v1/leetcode/cron/sync-all/ - run a sync for every linked account.

 Protected by a shared secret instead of JWT, because it's invoked by an
 external scheduler (GitHub Actions) without a user session.
 """
 permission_classes = (permissions.AllowAny,)
 throttle_classes = ()  # external scheduler should not be throttled

 def post(self, request):
 expected = settings.CRON_SHARED_SECRET
 if not expected:
 return Response({"detail": "Cron sync is disabled ..."},
 status=status.HTTP_503_SERVICE_UNAVAILABLE)

 provided = request.headers.get("X-Cron-Token", "")
 if not secrets.compare_digest(provided.encode(), expected.encode()):
 return Response({"detail": "Invalid token."}, ...)
 ...
```

Dhyaan dene wali do cheezein:

- **JWT ke bajaye shared secret**  -  GitHub Actions ke paas user login nahi hai, to JWT kahan se laaye? Ek random secret (`CRON_SHARED_SECRET`) dono jagah set kar diya (Render env + GitHub repo secret), aur woh `X-Cron-Token` header mein bheja jaata hai.
- **`secrets.compare_digest`**  -  yeh string comparison **constant-time** mein karta hai. Normal `==` early-exit karta hai jaise hi pehla mismatch character aaye  -  isse attacker timing measure karke secret guess kar sakta hai (timing attack). `compare_digest` har comparison mein same time leta hai chahe pehla char galat ho ya aakhri.

GitHub Actions side, `.github/workflows/scheduled-sync.yml`:

```yaml
on:
  schedule:
 - cron: "0 */6 * * *" # Every 6 hours (UTC)
  workflow_dispatch: {} # manual trigger from Actions tab

jobs:
  trigger-sync:
 steps:
 - name: Hit the cron sync endpoint
 run: |
 curl --silent --show-error --fail --max-time 120 \
 -X POST "$API_BASE_URL/api/v1/leetcode/cron/sync-all/" \
 -H "X-Cron-Token: $CRON_SHARED_SECRET"
```

Comment khud bolta hai: *"Replaces a Celery Beat worker on the free tier (Render free has no worker dyno)."* `--max-time 120` isiliye ki agar backend hang ho jaye to job slot na phans jaye. `--fail` se non-2xx response pe curl exit code non-zero deta, jisse GitHub Action red dikhega (monitoring).

**Toh phir beat schedule wala migration kyun rakha (point #4)?** Kyunki:
1. Dev mein abhi bhi tu asli Celery beat + worker chala sakta hai (Redis local pe hai). Tab schedule DB se padha jata hai.
2. Future mein agar paid tier pe shift karein, infra already wired hai  -  code touch karne ki zaroorat nahi, bas beat process start kar do.

Yeh ek "graceful degradation" design hai: ideal architecture (Celery beat) bhi maujood hai, aur free-tier reality (GitHub cron) bhi. Dono ek hi codebase mein co-exist karte hain.

---

#### 4. Migrations  -  schema evolution aur data migration

##### Migration hai kya

Tera Django model (`models.py`) Python class hai. Lekin database ko SQL tables chahiye. **Migration** woh bridge hai  -  woh ek file hai jo batati hai "database ko is state se us state mein le jao."

Do commands:

- **`makemigrations`**  -  tere models.py ko padhta hai, pichli migration se compare karta hai, aur farak ke liye ek **nayi migration file** banata hai. (Yeh DB ko touch nahi karta, sirf file banata hai.)
- **`migrate`**  -  pending migration files ko actually database pe **apply** karta hai (CREATE TABLE, ALTER TABLE, etc.) aur record karta hai ki kaunsi migration chal chuki (`django_migrations` table mein).

Har app ke `migrations/` folder mein numbered files hoti hain: `0001_initial.py`, `0002_...`, etc. Yeh **ordered** hain aur ek **dependency graph** banati hain. `0002` keh sakti "main `0001` ke baad chalungi", aur cross-app dependency bhi de sakti ("django_celery_beat ki migration 0019 ke baad chalungi"). Django is graph ko topological-sort karke sahi order mein apply karta hai.

##### Data migration  -  `0002_register_sync_schedule.py`

Zyaadatar migrations **schema** badalti hain. Lekin kabhi-kabhi tujhe schema nahi, **data** populate karna hota hai deploy ke time. Iske liye `RunPython` operation use hota.

`backend/apps/leetcode/migrations/0002_register_sync_schedule.py`:

```python
import json
from django.conf import settings
from django.db import migrations


def register_sync_schedule(apps, schema_editor):
 IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
 PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

 schedule, _ = IntervalSchedule.objects.get_or_create(
 every=settings.LEETCODE_SYNC_INTERVAL_HOURS,
 period="hours",
 )

 PeriodicTask.objects.update_or_create(
 name="leetcode.sync_all_accounts",
 defaults={
 "task": "leetcode.sync_all_accounts",
 "interval": schedule,
 "enabled": True,
 "kwargs": json.dumps({}),
 "description": (...),
 },
 )


def unregister_sync_schedule(apps, schema_editor):
 PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
 PeriodicTask.objects.filter(name="leetcode.sync_all_accounts").delete()


class Migration(migrations.Migration):
 dependencies = [
 ("leetcode", "0001_initial"),
 ("django_celery_beat", "0019_alter_periodictasks_options"),
 ]
 operations = [
 migrations.RunPython(register_sync_schedule, unregister_sync_schedule),
 ]
```

Ab yeh deeply samajh:

**Problem yeh solve kar raha hai:** `DatabaseScheduler` use kar rahe hain, yani beat ka schedule DB mein (`PeriodicTask` table) hota hai. Agar fresh deploy ho, woh table khaali hogi → beat ko pata hi nahi ki kya schedule karna hai. Koi insaan admin panel mein jaake manually schedule daale, yeh galat hai. Isiliye yeh migration deploy ke time **automatically** schedule register kar deti hai. Iska comment bhi yahi kehta: *"we want every fresh deploy to come up with the sync already wired without anyone clicking through admin."*

**`RunPython(forward, reverse)`**  -  do functions:
- `register_sync_schedule` = **forward** (jab `migrate` chale)
- `unregister_sync_schedule` = **reverse** (jab `migrate leetcode 0001` se rollback kare)

Reverse function dena best practice hai  -  taaki migration **reversible** rahe. Bina reverse ke `RunPython.noop` dena padta, aur rollback impossible ho jaata.

**`apps.get_model("django_celery_beat", "PeriodicTask")`  -  yeh sabse important concept hai.** Tu yahan seedha `from django_celery_beat.models import PeriodicTask` kyun nahi karta?

Kyunki migration **historical** hoti hai. Maan le aaj tu yeh migration likh raha hai, model mein 5 fields hain. 6 mahine baad library wale `PeriodicTask` mein naya field add kar dein. Agar tu real model import karta, to purani migration naye model ke against chalti  -  fields mismatch, crash. `apps.get_model()` woh model deta hai **jaisa woh us migration ke point pe tha** (migration state se reconstruct karke). Yeh "time-frozen" model hai. Isiliye migrations mein **hamesha** `apps.get_model()` use karo, kabhi direct import nahi.

**`get_or_create` aur `update_or_create` kyun?** Idempotency. Migration kabhi-kabhi dobara chal sakti (different DB, re-run). `create` use karte to "already exists" error aata. `get_or_create` / `update_or_create` se: agar nahi hai to bana do, hai to use/update kar do  -  kitni bhi baar chalao, end state same.

**Dependency graph mein `django_celery_beat` kyun?** Kyunki yeh migration `PeriodicTask` table ko likh rahi hai  -  woh table tab tak exist nahi karega jab tak `django_celery_beat` ki apni migrations (jo table banati hain) chal na jaayein. Isiliye humne explicitly bola "0019 ke baad chalo." Yeh cross-app ordering enforce karta.

---

#### 5. Caching  -  RedisCache vs LocMemCache

Caching ka idea: koi data jise baar-baar compute/fetch karna mehenga hai, usko ek tezz store mein rakh do, taaki agli baar seedha wahan se mile.

GrindMate prod mein, `base.py`:

```python
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
 "default": {
 "BACKEND": "django.core.cache.backends.redis.RedisCache",
 "LOCATION": REDIS_URL,
 "TIMEOUT": 300,
 }
}
```

- **`RedisCache`**  -  cache Redis (alag server) mein store hota. Iska fayda: tere multiple web processes (gunicorn workers) **same cache** share karte hain. Ek process ne set kiya, doosra padh sakta. Production mein yahi chahiye.
- **`TIMEOUT: 300`**  -  default 300 second (5 min) baad cache entry expire. Iske baad `cache.get()` `None` dega aur tujhe fresh compute karna hoga. Stale data se bachata.

Test mein, `test.py`:

```python
# In-memory cache so tests don't need Redis.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
```

- **`LocMemCache`**  -  cache **process ki RAM mein** ek Python dict ke roop mein store hota. Koi external server nahi. Fast, zero-setup.
- **Lekin caveat:** har process ka apna alag cache hota (shared nahi). Multi-process prod mein toot jaata  -  ek worker set kare, doosra na dekhe. Isiliye yeh **sirf dev/test** ke liye. Tests single-process mein chalte aur har test ke beech cache effectively reset (ya tests cache pe depend hi nahi karte), isiliye perfect.

Cache ki basic API (kahin bhi use karte ho):
```python
from django.core.cache import cache
cache.set("leaderboard:groupX", data, timeout=60)
value = cache.get("leaderboard:groupX") # miss pe None
cache.delete("leaderboard:groupX") # invalidate
```

Design rule jo GrindMate follow karta: cache layer ko **swappable** rakha  -  code `cache.get/set` likhta hai, backend (Redis vs LocMem) settings se aata. Code ko pata bhi nahi kaunsa backend hai. Yeh **dependency inversion** hai  -  yahi reason hai ki test mein bina Redis ke sab kaam karta.

---

#### 6. Testing stack  -  pytest + pytest-django

`backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "grindmate.settings.test"
python_files = ["test_*.py", "*_test.py", "tests.py"]
addopts = ["--strict-markers", "--reuse-db", "-ra"]
filterwarnings = ["ignore::DeprecationWarning"]
```

- **`DJANGO_SETTINGS_MODULE = "...test"`**  -  pytest ko bola test settings use kar (in-memory SQLite, fast hasher, etc.). Yeh `pytest-django` plugin ka config hai.
- **`--strict-markers`**  -  agar tu `@pytest.mark.foo` likhe jo registered nahi, error de. Typo (`@pytest.mark.djangodb`) silently skip nahi hoga.
- **`--reuse-db`**  -  har test run pe DB schema dobara create nahi karta, pichli baar ka reuse karta. Bahut tezz. (Schema badle to `--create-db` se force karna padta.)
- **`-ra`**  -  run ke end mein skipped/failed ka short summary deta.

##### `pytestmark = pytest.mark.django_db`

Har test file ke top pe yeh dikhega, jaise `test_api.py`:

```python
pytestmark = pytest.mark.django_db
```

Default mein `pytest-django` test ko DB **touch nahi karne deta** (safety  -  accidental prod DB write na ho). Jo test DB use karega usko `django_db` marker chahiye. `pytestmark` = module-level marker, yani us file ke **saare** tests ko mark kar deta (har function pe alag-alag lagane ki zaroorat nahi).

Under the hood: `django_db` marker har test ko ek **transaction** mein wrap karta hai aur test ke end mein **rollback** kar deta. Isiliye ek test ka data agle test mein leak nahi hota  -  har test fresh DB pe chalta. Yeh **isolation** ka core mechanism hai.

##### Fixtures, APIClient, force_authenticate

`test_api.py`:

```python
@pytest.fixture
def client() -> APIClient:
 return APIClient()

@pytest.fixture
def user():
 return UserFactory(username="anveet", email="anveet@grindmate.test")

@pytest.fixture
def authed_client(client, user) -> APIClient:
 client.force_authenticate(user=user)
 return client
```

- **Fixture** = reusable setup. Function arguments ke through inject hote hain. Jab test mein `def test_me_returns_user(self, authed_client, user):` likha, pytest dekhta hai inke naam ke fixtures hain, unhe build karke pass kar deta. `authed_client` khud `client` aur `user` fixtures pe depend karta  -  pytest dependency chain resolve karta.
- **`APIClient`**  -  DRF ka test client. Real server start nahi karta; URL resolve karke view ko directly call karta aur `Response` deta. Network nahi, bahut tezz.
- **`force_authenticate(user=user)`**  -  yeh JWT token banane, login karne ka jhanjhat skip kar deta. Seedha request ko "yeh user logged in hai" maan leta. Auth flow alag test karte (`TestLogin`), baaki tests mein bas authenticated state chahiye  -  to shortcut.

Ek strong test ka example (no-enumeration security behaviour):

```python
def test_resend_for_verified_user_is_silent(self, client, user):
 """Already-verified users get the same 202 (no enumeration)."""
 before = EmailVerificationToken.objects.filter(user=user).count()
 mail.outbox.clear()
 response = client.post(self.url, {"email": user.email}, format="json")
 assert response.status_code == status.HTTP_202_ACCEPTED
 assert EmailVerificationToken.objects.filter(user=user).count() == before
 assert mail.outbox == []
```

Yeh test sirf status code nahi, **side-effects** check kar raha  -  token count nahi badhna chahiye, email nahi jaani chahiye. Yeh is reasoning ko verify karta ki "verified user ko 202 to milega (taaki attacker ko pata na chale email exist karti), lekin actually kuch nahi hoga." Behaviour test, implementation test nahi.

---

#### 7. factory_boy  -  test data banane ka tezz tarika

Test ke liye objects chahiye  -  User, LeetCodeAccount, etc. Inhe manually `User.objects.create(...)` se banana boring + repetitive hai, aur har required field bharna padta. **factory_boy** isko declarative bana deta.

`backend/apps/users/factories.py`:

```python
class UserFactory(factory.django.DjangoModelFactory):
 class Meta:
 model = User
 django_get_or_create = ("email",)

 email = factory.Sequence(lambda n: f"user{n}@grindmate.test")
 username = factory.Sequence(lambda n: f"user{n}")
 display_name = factory.Faker("name")
 is_active = True
 is_email_verified = True

 @factory.post_generation
 def password(self, create, extracted, **kwargs):
 if not create:
 return
 self.set_password(extracted or "testpass123!")
 self.save()
```

Concepts:

- **`DjangoModelFactory`**  -  base class, `Meta.model` se bata diya kaunsa model banana.
- **`Sequence(lambda n: f"user{n}@...")`**  -  har naye object ke liye `n` badhta jaata (0,1,2…). Isse **unique** email/username milta. Important kyunki email/username unique hain DB mein  -  fixed value dete to second `UserFactory()` IntegrityError deta.
- **`Faker("name")`**  -  random realistic naam generate karta (e.g. "Priya Sharma"). Test data realistic dikhta.
- **`django_get_or_create = ("email",)`**  -  agar usi email ka user pehle se hai to naya nahi banayega, existing return karega. Tests mein yeh bahut helpful  -  jaise `test_api.py` ka `user` fixture `email="anveet@grindmate.test"` deta, aur agar koi aur jagah wahi email aaye to clash nahi hoga.
- **`@factory.post_generation` password**  -  sabse zaroori detail. Object banne ke **baad** chalne wala hook. Password ko seedha set nahi kar sakte  -  usse hash karna padta (`set_password`), warna `check_password` test fail hoga. Yeh hook `extracted or "testpass123!"` use karta  -  yani agar `UserFactory(password="xyz")` doge to "xyz", warna default "testpass123!". Isiliye tests mein har jagah login ke liye `"testpass123!"` use hota (`test_login_returns_tokens_and_user`).

`backend/apps/leetcode/factories.py` mein **`SubFactory`** dekhta hai:

```python
class SubmissionLogFactory(factory.django.DjangoModelFactory):
 class Meta:
 model = SubmissionLog
 user = factory.SubFactory(UserFactory)
 problem = factory.SubFactory(ProblemFactory)
 solved_at = factory.LazyFunction(timezone.now)
 source = SubmissionLog.SOURCE_AUTO
```

- **`SubFactory(UserFactory)`**  -  `SubmissionLog` ko ek `user` aur `problem` (foreign keys) chahiye. SubFactory automatically related object bhi bana deta. Yani `SubmissionLogFactory()` ek call mein user + problem + submission teeno bana deta. Agar tu `SubmissionLogFactory(user=existing)` de, to woh existing use karega, naya nahi banayega.
- **`LazyFunction(timezone.now)`**  -  `timezone.now` ko **object banne ke time** call karta. Agar seedha `solved_at = timezone.now()` likhte (without Lazy), to woh value **factory class load hone ke time** ek baar evaluate hoti aur sab objects ko same purana timestamp milta. Lazy se har object ko fresh "now" milta. (`Sequence` bhi lazy hi hai, ek tarah se.)

`test_managers.py` mein iska direct use:

```python
def test_by_difficulty_returns_counts():
 user = UserFactory()
 SubmissionLogFactory.create_batch(2, user=user, problem=ProblemFactory(difficulty="easy"))
 SubmissionLogFactory(user=user, problem=ProblemFactory(difficulty="medium"))
 counts = SubmissionLog.objects.for_user(user).by_difficulty()
 assert counts == {"easy": 2, "medium": 1}
```

`create_batch(2, ...)` ek shot mein 2 objects banata. Notice manually 3 SubmissionLog + 2 Problem + 1 User likhne ki jagah factories ne 3 lines mein kar diya  -  yahi factory_boy ka asli fayda.

**Factories vs fixtures (Django ke `.json` fixtures):** Purane Django fixtures static JSON hote  -  har baar wahi data, badalna mushkil, schema badle to toot jaate. Factories **dynamic + programmatic** hain  -  test mein jo chahiye woh override kar do (`difficulty="easy"`), baaki defaults factory bhar deta. Maintainable aur readable.

---

#### 8. responses library  -  external HTTP calls ko mock karna

Yeh testing philosophy ka dil hai. **Test mein kabhi asli LeetCode ko call mat karo.** Kyun?

1. **Speed**  -  network call slow hai; test milliseconds mein chahiye.
2. **Determinism**  -  asli LeetCode kabhi up, kabhi down, kabhi rate-limit. Test ka result tere code pe depend karna chahiye, kisi external server ke mood pe nahi.
3. **No side-effects / offline**  -  CI machine internet ke bina bhi test chala sake; LeetCode ko spam na ho.
4. **Edge cases**  -  "user not found", "429 rate limit", "500 error"  -  yeh asli server se on-demand laana impossible. Mock se aaram se simulate.

`responses` library `requests` ke HTTP calls ko intercept karta hai aur tere diye fake response deta  -  asli network kabhi nahi jaata.

`test_sync.py`:

```python
@responses.activate
def test_sync_creates_placeholder_problems_and_submissions():
 user = UserFactory()
 account = LeetCodeAccountFactory(user=user, handle="anveet", sync_status=SyncStatus.PENDING)
 responses.post(LC_URL, json=_profile_response("anveet"))
 responses.post(LC_URL, json=_recent_response())

 result = sync_account(account)

 assert result.error is None
 assert result.new_solves == 2
 assert result.problems_resolved == 2
 assert len(responses.calls) == 2  # no per-problem call
 ...
```

- **`@responses.activate`**  -  decorator jo us test ke andar `requests` ko intercept-mode mein daal deta. Bahar nikalte hi normal.
- **`responses.post(LC_URL, json=...)`**  -  "agar koi `LC_URL` pe POST kare, yeh JSON return kar do." Humne do register kiye  -  pehla profile, doosra recent. `responses` inhe **order mein** queue karta: pehla matching call ko pehla response, doosre ko doosra.
- **`len(responses.calls) == 2`**  -  yeh assertion ek **architecture decision verify kar raha**. `sync.py` mein `defer_meta=True` wala refactor hua tha  -  sync ke time per-problem metadata fetch **nahi** karte (woh slow hai). Pehle har naye problem pe ek extra LeetCode call jaati (2 + N calls). Refactor ke baad sirf 2 calls (profile + recent), problems placeholder banake chhod dete:

```python
# sync.py - upsert_problem
if defer_meta:
 return Problem.objects.create(
 title_slug=slug,
 title=fallback_title or slug.replace("-", " ").title(),
 difficulty="", # placeholder
 topic_tags=[],
 is_premium=False,
 )
```

Aur test isi ko pakadta:
```python
# Placeholders have empty difficulty until backfill runs.
assert set(Problem.objects.values_list("difficulty", flat=True)) == {""}
```

Yani test sirf "kaam hua" nahi, "kaam **efficiently** hua (sirf 2 network calls, bounded latency)" bhi guarantee kar raha. Agar koi galti se per-problem call wapas add kare, `len(responses.calls) == 2` fail ho jayega  -  yeh ek **performance regression guard** hai.

**Retry behaviour mock karna**  -  `test_services.py`:

```python
@responses.activate
def test_rate_limit_retries_then_raises():
 # 3 attempts × 429 → final raise
 for _ in range(3):
 responses.post(LC_URL, status=429, body="rate limit")
 with pytest.raises(LeetCodeRateLimited):
 fetch_profile_summary("anveet")

@responses.activate
def test_rate_limit_then_recovers():
 responses.post(LC_URL, status=429, body="slow down") # 1st call: fail
 responses.post(LC_URL, json=_profile_payload()) # 2nd call: succeed
 summary = fetch_profile_summary("anveet")
 assert summary.handle == "anveet"
```

`services.py` ka `tenacity` retry (`stop_after_attempt(3)`) yahan test ho raha  -  3 baar 429 do to teeno baad raise; ek baar 429 fir success do to retry karke recover ho jaata. Note: yahan asli backoff wait skip ho jaata (tenacity test mein bhi waits leta, lekin yeh min=2s waits hai  -  practically test thoda slow ho sakta, lekin deterministic). Important: humne **Celery ke autoretry pe nahi, tenacity (HTTP-level retry) pe** test likha  -  yeh decision point #2 (eager mode) se juda hai: eager mode mein Celery retry reliably test nahi hota, isiliye retry logic ko ek level neeche (service layer) push karke wahan test kiya.

---

#### 9. freezegun  -  time ko freeze karna

Kuch logic time pe depend karta  -  token expiry, "aaj solve hua kya", streak count. Asli `now()` test mein use karo to test **non-deterministic** ho jaata (aaj pass, kal fail). **freezegun** time ko fix kar deta.

`test_managers.py`:

```python
@pytest.fixture
def fixed_now():
 """Freeze 'now' on a Wednesday."""
 with freeze_time("2026-05-06 12:00:00") as frozen:  # Wednesday
 yield frozen

def test_this_week_returns_monday_to_monday(fixed_now):
 user = UserFactory()
 inside_week = SubmissionLogFactory(user=user, solved_at=timezone.now() - timedelta(days=2))
 outside_week = SubmissionLogFactory(user=user, solved_at=timezone.now() - timedelta(days=10))
 qs = SubmissionLog.objects.for_user(user).this_week()
 assert list(qs) == [inside_week]
```

`freeze_time("2026-05-06")` ke andar `timezone.now()` hamesha woh fixed Wednesday dega. Isse "this week" (Monday-to-Monday) ka boundary test deterministic ban jaata  -  2 din pehle wala andar, 10 din pehle wala bahar. Bina freeze ke yeh test din-ke-hisaab se kabhi pass kabhi fail karta.

Yeh ek fixture mein wrap karke `yield` kiya  -  `yield` ke pehle setup (freeze on), test chalta, baad mein teardown (freeze off). Token-expiry tests mein bhi yahi pattern: time aage badhao (`freeze_time` ko move karke) aur check karo token ab expired hai ya nahi  -  bina actually 7 din wait kiye.

---

#### 10. Test settings  -  kyun kya optimize kiya

`backend/grindmate/settings/test.py` ek ek line **deliberately** test ko fast/isolated banane ke liye hai:

```python
# In-memory SQLite for speed.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Don't hash passwords during tests - speeds up factory_boy user creation.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory cache so tests don't need Redis.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Run Celery tasks synchronously, no broker needed.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
```

- **`:memory:` SQLite**  -  DB RAM mein, disk pe nahi. Process khatam to gone. Ultra-fast, zero cleanup. (CI mein actual Postgres use hota  -  `ci.yml` mein `DATABASE_URL` set hai  -  taaki "prod jaisa DB" pe bhi sanity rahe; local pytest in-memory SQLite.)
- **`MD5PasswordHasher`**  -  prod mein password Argon2/PBKDF2 se hash hota, jo **deliberately slow** hai (brute-force rokne ko). Lekin har `UserFactory()` ek password hash karta  -  agar slow hasher use karein to 100 user banane mein test ke seconds barbad. MD5 fast (insecure, lekin test mein security matter nahi karti  -  sirf "hash hua ki nahi" logic chahiye). Yeh **sabse common test-speed trick** hai Django mein.
- **`locmem` email backend**  -  email actually nahi bhejti, ek in-memory list `django.core.mail.outbox` mein store karti. Isiliye `test_api.py` mein `assert len(mail.outbox) == 1` aur `mail.outbox[0].to == [unverified.email]` likh paaye  -  bina asli SMTP ke verify kar liya ki email "trigger hui aur sahi address pe."
- **Throttle rates `100000/hour`**  -  prod mein register `10/hour`, password_reset `5/hour` hai. Test mein agar ek class ke andar 5 register calls karein to throttle hit ho jaata aur test 429 se fail hota  -  lekin woh real bug nahi, sirf test ka byproduct. Astronomically high rate se throttling effectively off, par code-path (throttle classes) attached rehte (so config tootne pe pata chale).

Ek hi codebase, teen settings files (`development`, `test`, `production`)  -  sab `base.py` se inherit (`from .base import *`). Yeh **12-factor / settings-per-environment** pattern hai: code ek, behaviour environment se. `pyproject.toml` ne `DJANGO_SETTINGS_MODULE = "...test"` set kar diya, to pytest hamesha test settings uthata.

---

#### 11. Tests chalana  -  practical commands

Saare commands `backend/` directory se (jahan `pyproject.toml` hai), virtualenv active hone par:

```bash
pytest # saare tests
pytest -q # quiet - kam output, sirf dots
pytest -x # pehli failure pe ruk jao (fail-fast)
pytest --cov # coverage ke saath (pyproject mein source=apps,grindmate)
pytest --cov --cov-report=term-missing # konsi lines cover nahi huiं dikha
pytest apps/leetcode/tests/test_sync.py # ek file
pytest apps/leetcode/tests/test_sync.py::test_sync_is_idempotent_for_same_solves # ek test
pytest -k "rate_limit" # naam mein "rate_limit" wale saare tests
pytest --create-db # schema badla ho to DB dobara banao (--reuse-db override)
```

`-ra` (pyproject mein already on)  -  end mein summary deta. `--cov-report=term-missing` se woh **lines** dikhti jo kisi test ne touch nahi ki  -  yeh "kya bacha hai test karne ko" ka map hai.

##### Failing test kaise padhe

Jab test fail hota, pytest yeh deta:
1. **kaunsa test**  -  `FAILED apps/leetcode/tests/test_sync.py::test_sync_... `
2. **assertion ka diff**  -  `assert 1 == 2` style, dono values dikhata (pytest "assertion rewriting" karta  -  isiliye plain `assert` bhi rich output deta, `assertEqual` ki zaroorat nahi)
3. **traceback**  -  kis line pe toota

Strategy: pehle `pytest -x` se sabse pehli failure pakdo (cascade mein baaki failures often usi ka side-effect hote). Fir us ek test ko akela chalao (`::test_name`) taaki noise kam ho. Fir assertion diff padho  -  "expected X, got Y" se seedha clue milta. Zyaadatar failures isolation-related nahi hote (kyunki `django_db` rollback isolate karta), balki actual logic ya mock-setup (galat `responses.post` count) ki wajah se hote.

---

#### Common galtiyan / gotchas

1. **Task ko object pass karna**  -  `sync_account_task.delay(account)` likhna galat. Object JSON-serializable nahi (ya stale ho jaayega jab tak worker uthayega). Hamesha `id` pass karo aur task ke andar `objects.get(pk=id)` karo  -  jaisa GrindMate karta hai.
2. **Migration mein direct model import**  -  `from django_celery_beat.models import PeriodicTask` likhna gotcha. Future mein model badla to purani migration tootegi. Hamesha `apps.get_model()`.
3. **`EAGER_PROPAGATES` bhoolna**  -  sirf `ALWAYS_EAGER = True` set karke `EAGER_PROPAGATES` na karna → buggy task test mein silently pass. Dono saath chahiye.
4. **`django_db` marker bhoolna**  -  DB use karne wale test pe marker nahi to `RuntimeError: Database access not allowed`. `pytestmark` top pe lagao.
5. **`LazyFunction` na use karna**  -  `solved_at = timezone.now()` (without Lazy) factory mein → sab objects ko ek hi purana timestamp. Time-based test silently galat. `LazyFunction(timezone.now)` use karo.
6. **`responses` register karna bhool jaana**  -  agar `@responses.activate` ke andar koi call register nahi ki to woh `ConnectionError` dega (real call block hota). Yeh actually achi baat hai  -  galti se internet pe jaana fail ho jaata.
7. **Slow password hasher**  -  agar test settings mein MD5 hasher na set karo, hundreds of `UserFactory()` se test suite seconds slow ho jaata. Yeh sabse common "tests slow hain" ki wajah.
8. **LocMemCache pe multi-process bharosa**  -  kabhi prod mein LocMemCache mat chhodna; cache process-local hota, doosra worker miss karega.

---

#### Interview Questions + short answers

**Q1. Celery mein broker aur result backend mein kya farak?**
Broker (Redis) woh queue hai jahan task **bheje** jaate hain worker ke liye. Result backend (yahan `django-db`) woh store hai jahan task ka **return value/status** rakha jaata read karne ke liye. Dono alag responsibilities  -  ek "kaam bhejna", doosra "natija rakhna."

**Q2. `bind=True` kab chahiye?**
Jab task ke andar task instance (`self`) chahiye  -  manual `self.retry()`, `self.request.id`, ya retry count access karne ke liye. Bina `bind=True` ke `self` nahi milta.

**Q3. `CELERY_TASK_ALWAYS_EAGER` kya karta aur kahan use hota?**
Yeh `.delay()` ko broker mein bhejne ke bajaye task ko **usi process mein synchronously** chala deta. Dev/test mein use hota taaki Redis aur worker ki zaroorat na pade  -  tests fast aur self-contained rehte.

**Q4. GrindMate prod mein Celery beat kyun nahi use karta, kya use karta hai?**
Render free tier pe alag worker dyno nahi milta, to beat/worker chal hi nahi sakte. Iski jagah ek **GitHub Actions scheduled workflow** har 6 ghante ek shared-secret-protected HTTP endpoint (`/cron/sync-all/`) hit karta, jo synchronously sync chala deta  -  beat ka replacement.

**Q5. Data migration mein `apps.get_model()` kyun, direct import kyun nahi?**
`apps.get_model()` model ka **historical** version deta (jaisa migration likhte time tha). Direct import current model deta, jo future mein badal sakta  -  tab purani migration crash karegi. Migration reproducible rahe isiliye historical model chahiye.

**Q6. `pytest.mark.django_db` kya guarantee deta?**
Test ko DB access allow karta aur test ko ek transaction mein wrap karke end pe rollback kar deta  -  isse har test isolated rehta, ek ka data doosre mein leak nahi hota.

**Q7. `responses` library ka test mein kya role?**
Yeh `requests` ke HTTP calls intercept karke fake response deta  -  asli LeetCode kabhi call nahi hota. Isse tests fast, deterministic, offline-capable bante, aur edge cases (429, user-not-found) easily simulate hote.

**Q8. Test settings mein MD5PasswordHasher kyun?**
Prod ke secure hashers (Argon2/PBKDF2) deliberately slow hain. Har factory user password hash karta  -  slow hasher se test suite kaafi slow ho jaata. MD5 fast hai aur test mein security matter nahi karti, sirf hashing logic chahiye.

**Q9. `sync_all_accounts` fan-out pattern ke fayde?**
Dispatcher task khud kaam nahi karta, har account ke liye alag task queue karta. Isse parallelism (multiple workers), isolation (ek account fail to baaki chalte), aur per-account retry granularity milti.

**Q10. `len(responses.calls) == 2` assertion kya verify kar raha?**
Yeh `defer_meta` refactor ko guard karta  -  sync ke time per-problem metadata fetch **nahi** hona chahiye, sirf 2 calls (profile + recent). Yeh ek performance regression guard hai: koi galti se per-problem call wapas add kare to yeh test fail ho jayega.

---

#### Khud try kar (exercises)

1. **Naya periodic task register kar (data migration).** Maan le tu chahta hai har 24 ghante ek "cleanup expired tokens" task chale. `apps/users/` mein ek nayi data migration likh jo `IntervalSchedule(every=24, period="hours")` aur ek `PeriodicTask` register kare  -  bilkul `0002_register_sync_schedule.py` ke pattern pe. Reverse function bhi likhna. Fir `python manage.py migrate users` chalakar admin mein `Periodic Tasks` mein dekh ki entry aayi.

2. **Ek failing-network test likh.** `test_services.py` mein ek naya test add kar jo `responses.post(LC_URL, body=requests.exceptions.ConnectionError())` use karke network failure simulate kare, aur assert kare ki `fetch_profile_summary` `LeetCodeAPIError` raise karta hai (`services.py` ka `except requests.RequestException` branch). Hint: `responses.post(..., body=ConnectionError("boom"))`.

3. **Time-travel token expiry test.** `test_managers.py` ke `freeze_time` pattern use karke ek test likh: ek `EmailVerificationToken` banao "aaj", fir `freeze_time` ko token ki expiry se aage le jaakar (e.g. 25 ghante baad) assert karo ki token ab invalid/expired treat hota hai. Dekh ki bina actually wait kiye time-dependent logic kaise test hota.


---


## 7. Ek Request ki Poori Journey (End-to-End Lifecycle)

Ab tak humne tukdo-tukdo mein padha  -  URLs alag, views alag, serializers alag, middleware alag. Is chapter mein hum do ACTUAL requests lenge aur unhe gunicorn se le kar JSON response tak, har ek layer se guzaarenge. Jab tu yeh do traces samajh lega, tujhe poora Django/DRF ka "data flow" ka mental model clear ho jayega. Chai bana le, baith ja, dhyaan se.

Do requests:

- **REQUEST A**  -  `POST /api/v1/auth/login/`  -  anonymous (koi token nahi). Yeh dikhayega: middleware stack, URL routing, DRF authentication/permission/throttle, serializer validation, JWT minting.
- **REQUEST B**  -  `GET /api/v1/groups/<uuid>/leaderboard/?period=weekly`  -  authenticated (Bearer token ke saath). Yeh dikhayega: JWT decode, object-level permission, cache hit/miss, annotated ORM query, dataclass-to-serializer shape.

---

#### 0. Pehle bada picture  -  request aati kahan se hai?

```
Browser/React app
 │  HTTP request (TCP)
 ▼
┌--------------------------------------┐
│  gunicorn  (WSGI HTTP server) │ ← process jo port pe sun raha hai
│ - master process + N worker procs │
└--------------------------------------┘
 │  WSGI protocol (environ dict + start_response callable)
 ▼
┌--------------------------------------┐
│  Django WSGIHandler │ grindmate/wsgi.py -> application
│ (settings.WSGI_APPLICATION) │
└--------------------------------------┘
 │
 ▼
 MIDDLEWARE stack  →  URL resolver  →  View  →  ... (neeche detail)
```

Samajh le yeh teen alag cheezein hain jo log aksar gadbad kar dete hain:

- **gunicorn**  -  yeh ek WSGI *server* hai. Iska kaam: TCP socket pe sunna, raw HTTP bytes ko parse karna, aur har request ko ek Python dict (`environ`) mein convert karke Django ko de dena. gunicorn ke paas N worker processes hote hain  -  har worker ek request ek time pe handle karta hai (sync worker). Yahi reason hai ki `EMAIL_TIMEOUT = 10` settings mein hai (`base.py:216`)  -  agar SMTP handshake hang ho gaya, toh ek poora gunicorn worker block ho jaata, isiliye cap lagaya.
- **WSGI**  -  yeh koi software nahi, ek *contract/interface* hai (PEP 3333). Bolta hai: "server, tu mujhe `environ` dict aur `start_response` function dega; main tujhe response body ka iterable return karunga." gunicorn aur Django dono is contract ko follow karte hain, isiliye ek-doosre se baat kar paate hain.
- **Django**  -  actual application. `WSGI_APPLICATION = "grindmate.wsgi.application"` (`base.py:87`) batata hai entry-point kahan hai.

---

#### 1. REQUEST A  -  `POST /api/v1/auth/login/` (anonymous)

Request aisi hai:

```http
POST /api/v1/auth/login/ HTTP/1.1
Host: api.grindmate.app
Content-Type: application/json

{"email": "anveet@example.com", "password": "hunter2"}
```

##### 1.1 The Onion  -  middleware "request neeche, response upar"

Django ka middleware ek **onion (pyaaz)** ki tarah hota hai. Request bahar se andar (top-to-bottom) jaati hai, view hit hoti hai, phir response andar se bahar (bottom-to-top) wapas aati hai. Yeh **galti** mat karna ki middleware ek list hai jo bas top-to-bottom chalti hai  -  yeh do baar chalti hai, ulti direction mein.

Hamari `MIDDLEWARE` list (`base.py:58-68`):

```python
MIDDLEWARE = [
 "django.middleware.security.SecurityMiddleware", # 1
 "whitenoise.middleware.WhiteNoiseMiddleware", # 2
 "corsheaders.middleware.CorsMiddleware", # 3
 "django.contrib.sessions.middleware.SessionMiddleware", # 4
 "django.middleware.common.CommonMiddleware", # 5
 "django.middleware.csrf.CsrfViewMiddleware", # 6
 "django.contrib.auth.middleware.AuthenticationMiddleware",# 7
 "django.contrib.messages.middleware.MessageMiddleware", # 8
 "django.middleware.clickjacking.XFrameOptionsMiddleware", # 9
]
```

```
 REQUEST A: POST /api/v1/auth/login/

 ┌-----------------------------------------------------------------┐
 │ gunicorn worker → WSGI environ → Django WSGIHandler │
 └-----------------------------------------------------------------┘
 │ request neeche jaa rahi (top → bottom) ▲ response upar
 ▼ │ (bottom → top)
 ┌---------------------------------------------------------------┐
 │ 1. SecurityMiddleware HTTPS redirect, HSTS header daalta │
 │  ┌----------------------------------------------------------┐ │
 │  │ 2. WhiteNoise /static/* hai? to yahin se file serve, │ │
 │  │ warna aage bhej. (login /static nahi → aage)│ │
 │  │ ┌--------------------------------------------------------┐ │ │
 │  │ │ 3. CorsMiddleware  Origin check, response pe │ │ │
 │  │ │ Access-Control-Allow-* headers chipkata │ │ │
 │  │ │ ┌------------------------------------------------------┐│ │ │
 │  │ │ │ 4. SessionMiddleware  cookie se session resolve ││ │ │
 │  │ │ │ ┌----------------------------------------------------┐│ │ │
 │  │ │ │ │ 5. CommonMiddleware  APPEND_SLASH, etc. ││ │ │
 │  │ │ │ │ ┌--------------------------------------------------┐│ │ │
 │  │ │ │ │ │ 6. CsrfViewMiddleware  (DRF JWT pe exempt - neeche)││ │ │
 │  │ │ │ │ │ ┌------------------------------------------------┐│ │ │
 │  │ │ │ │ │ │ 7. AuthenticationMiddleware  request.user = ││ │ │
 │  │ │ │ │ │ │ lazy SessionUser (DRF baad mein override) ││ │ │
 │  │ │ │ │ │ │ ┌----------------------------------------------┐│ │ │
 │  │ │ │ │ │ │ │ 8. Messages  9. XFrameOptions ││ │ │
 │  │ │ │ │ │ │ │ ┌--------------------------------------------┐│ │ │
 │  │ │ │ │ │ │ │ │ URL RESOLVER → DRF VIEW (CORE - sec 1.3)  ││ │ │
 │  │ │ │ │ │ │ │ │ LoginView → serializer → JWT mint ││ │ │
 │  │ │ │ │ │ │ │ └--------------------------------------------┘│ │ │
 │  │ │ │ │ │ │ └----------------------------------------------┘│ │ │
 │  │ │ │ │ │ └------------------------------------------------┘│ │ │
 │  │ │ │ │ └--------------------------------------------------┘│ │ │
 │  │ │ │ └----------------------------------------------------┘│ │ │
 │  │ │ └------------------------------------------------------┘│ │ │
 │  │ └--------------------------------------------------------┘ │ │
 │  └----------------------------------------------------------┘ │
 └---------------------------------------------------------------┘
 ▼ JSON {access, refresh, user} 200 OK wapas client ko
```

**Kya hai / kyun / under the hood:** Modern Django (1.10+) "new-style" middleware use karta hai. Har middleware ek callable hai jise `get_response` (agla middleware ya view) inject hota hai. Conceptually:

```python
class SomeMiddleware:
 def __init__(self, get_response):
 self.get_response = get_response # ek baar startup pe

 def __call__(self, request):
 # --- request neeche jaane wala code (pre-view) ---
 response = self.get_response(request)  # agle layer ko call -> recursion andar
 # --- response upar aane wala code (post-view) ---
 return response
```

Toh `__call__` ke pehle wala part **top-to-bottom** chalta hai (request andar ja rahi), aur `self.get_response(request)` ke baad wala part **bottom-to-top** chalta hai (response bahar aa rahi). Isiliye `SecurityMiddleware` request pe pehla hai, par HSTS/security headers response mein **last** mein chipakte hain (jab response wapas top tak pahunchti hai).

**Order kyun maayne rakhta hai:**

- `CorsMiddleware` ko `CommonMiddleware` se **upar** rakha gaya  -  corsheaders docs explicitly bolte hain ki CORS headers tab bhi lagne chahiye jab CommonMiddleware ek redirect generate kar de. Galat order mein OPTIONS preflight fail ho jaata aur React app `CORS error` deta.
- `SessionMiddleware` `AuthenticationMiddleware` se upar  -  kyunki auth middleware ko `request.session` chahiye user resolve karne ke liye. Niche-upar ka dependency hai.
- `WhiteNoise` upar ki taraf  -  taaki static files (CSS/JS) ke liye request poori auth/session machinery se na guzre, seedha file serve ho jaaye. Performance optimization.

**Gotcha (CSRF + JWT):** Yeh anonymous JSON POST hai phir `CsrfViewMiddleware` block kyun nahi karta? Do reasons: (a) DRF ki `APIView` `csrf_exempt` hai middleware-level pe; CSRF enforcement DRF ke andar sirf `SessionAuthentication` ke liye hota hai. (b) Login pe humara primary auth JWT hai, session nahi  -  toh DRF CSRF check skip kar deta hai. Isiliye token-based API ko CSRF token bhejne ki zaroorat nahi.

##### 1.2 URL resolver  -  routing kaise hoti hai

Middleware ke baad Django URL resolver chalta hai. `ROOT_URLCONF = "grindmate.urls"` (`base.py:70`) se shuru:

```python
# grindmate/urls.py:18-28
api_v1_patterns = [
 path("auth/", include("apps.users.urls")),
 path("leetcode/", include("apps.leetcode.urls")),
 path("groups/", include("apps.groups.urls")),
]
urlpatterns = [
 path("admin/", admin.site.urls),
 path("health/", healthcheck, name="healthcheck"),
 path("api/v1/", include((api_v1_patterns, "v1"), namespace="v1")),
]
```

Resolver path ko **prefix-by-prefix** match karta hai, har match ke baad woh hissa "kha kar" baaki string aage `include`-d urlconf ko deta hai:

```
/api/v1/auth/login/
 ├- "api/v1/"  match → bacha: "auth/login/" → api_v1_patterns mein dhoondho
 │ └- "auth/" match → bacha: "login/" → apps.users.urls mein dhoondho
 │ └- "login/" match → bacha: "" → views.LoginView.as_view()
```

`apps/users/urls.py:12`:

```python
path("login/", views.LoginView.as_view(), name="login"),
```

**Under the hood  -  `as_view()` kya karta hai:** `LoginView.as_view()` ek class nahi, ek **function** (closure) return karta hai. Yeh function har request pe ek **naya** `LoginView` instance banata hai (`self = cls(**initkwargs)`), `self.request`, `self.args`, `self.kwargs` set karta hai, aur `self.dispatch(request)` call karta hai. Yeh design important hai  -  har request ka apna fresh view instance hota hai, isiliye `self` pe state rakhna thread-safe hai (ek view instance do requests ke beech share nahi hota).

##### 1.3 DRF dispatch  -  gatekeepers ka sequence

`LoginView` (`apps/users/views.py:42-46`):

```python
class LoginView(TokenObtainPairView):
 serializer_class = GrindMateTokenObtainPairSerializer
 permission_classes = (permissions.AllowAny,)
```

`TokenObtainPairView` DRF ka `APIView` hai. Jab `dispatch()` chalta hai, DRF `initial(request)` call karta hai jo **3 gatekeepers** is order mein chalata hai:

```
dispatch()
  └- initialize_request()  → DRF Request object banta hai (regular HttpRequest ko wrap karke)
  └- initial(request):
 1. perform_authentication()  → request.user touch karta (lazy)
 2. check_permissions() → har permission_class ka has_permission()
 3. check_throttles() → har throttle ka allow_request()
  └- handler = self.post  (HTTP method → method name mapping)
  └- response = handler(request)
```

Login ke liye:

1. **Authentication classes**  -  `DEFAULT_AUTHENTICATION_CLASSES` (`base.py:136-139`) hai `(JWTAuthentication, SessionAuthentication)`. Anonymous login request mein koi `Authorization` header nahi, koi session cookie nahi  -  toh dono authenticators `None` return karte hain → `request.user = AnonymousUser`. Yeh **fail nahi** hota; bas user anonymous reh jaata hai.

2. **Permission**  -  `permission_classes = (AllowAny,)`. Yeh explicitly default `IsAuthenticated` (`base.py:140`) ko override karta hai. **Kyun zaroori hai:** agar `AllowAny` na lagaate, toh global default `IsAuthenticated` chalta aur anonymous user login hi nahi kar paata  -  chicken-and-egg problem (login karne ke liye pehle se login chahiye). `AllowAny.has_permission()` hamesha `True` return karta hai.

3. **Throttle**  -  koi explicit `throttle_classes` `LoginView` pe nahi, toh global `DEFAULT_THROTTLE_CLASSES` (`base.py:144-147`) chalte hain: `AnonRateThrottle` + `UserRateThrottle`. User anonymous hai, toh `AnonRateThrottle` apply hota hai  -  `60/hour` per IP (`base.py:150`). Under the hood: throttle client IP ka cache key banata hai (`throttle_anon_<ip-hash>`), Redis cache mein us IP ke last requests ke timestamps store karta hai, sliding window mein count karta hai; 60 cross hua toh `429 Too Many Requests` raise.

##### 1.4 Handler → serializer → JWT mint

Tino gatekeepers pass ho gaye, ab `self.post()` chalta hai (yeh `TokenObtainPairView.post` hai). Woh serializer ko request data deta hai aur `serializer.is_valid(raise_exception=True)` call karta hai. Asli kaam humare custom serializer mein hota hai:

```python
# apps/users/serializers.py:56-75
class GrindMateTokenObtainPairSerializer(TokenObtainPairSerializer):
 @classmethod
 def get_token(cls, user):
 token = super().get_token(user)
 token["username"] = user.username
 return token

 def validate(self, attrs):
 data = super().validate(attrs) # ← credentials check + token mint
 if not self.user.is_email_verified: # ← email-verified gate
 raise exceptions.AuthenticationFailed(
 "Email not verified. ...",
 code="email_not_verified",
 )
 data["user"] = UserSerializer(self.user).data # ← extra payload
 return data
```

Step-by-step `validate()` ke andar:

- `super().validate(attrs)` (simplejwt ka base) yeh karta hai:
  - `authenticate(username=..., password=...)` call karta hai → Django ke auth backend pe jaata hai → `User.check_password()` → password hash compare (PBKDF2/Argon2, `settings.PASSWORD_HASHERS`). Galat password → `AuthenticationFailed` → DRF isko `401` mein convert karta hai.
  - Sahi hua toh `self.user` set hota hai aur `RefreshToken.for_user(self.user)` se ek **refresh token** banta hai, jisme se `access` token derive hota hai. Yahan `get_token()` override hua hai  -  har token ke payload mein `username` claim extra ghusaaya gaya, taaki frontend ko bina decode karke kaam aa jaaye.
  - Returns `{"refresh": "...", "access": "..."}`.
- **Email-verified gate**  -  yeh GrindMate-specific business rule hai. simplejwt by default email-verified ka koi concept nahi rakhta. Hum `self.user.is_email_verified` check karte hain; verified nahi toh `AuthenticationFailed` (`401`) with a custom `code="email_not_verified"`  -  frontend is code pe "Resend verification" button dikha sakta hai.
- `data["user"] = UserSerializer(self.user).data`  -  yeh ek **deliberate design decision** hai. Comment bhi bolta hai (`serializers.py:57-58`): "frontend avoids a second `/me` round-trip on login." Matlab login response mein hi poora user object bhej do, taaki React app ko login ke turant baad `GET /me/` na maarna pade. Ek HTTP round-trip bach gaya.

**Under the hood  -  JWT kya hota hai:** JWT = teen base64url hisson ka string `header.payload.signature`. Payload mein claims hote hain  -  `user_id` (`USER_ID_CLAIM = "user_id"`, `base.py:170`), `exp` (expiry), `token_type`, aur humara custom `username`. Signature = `HMAC-SHA256(header.payload, SECRET_KEY)`. Server stateless hai  -  token mein hi sab info hai, server ko DB mein "session" store nahi karni padti. Access token 15 min jeeta hai (`ACCESS_TOKEN_LIFETIME`, `base.py:160-162`), refresh 7 din.

Response object banta hai: `Response({"access": ..., "refresh": ..., "user": {...}})` with `200 OK`. Yeh **bottom-to-top** sare middleware se wapas guzarta hai  -  CorsMiddleware `Access-Control-Allow-Origin` chipkata hai, SecurityMiddleware HSTS header, etc.  -  aur gunicorn JSON bytes client ko bhej deta hai.

---

#### 2. REQUEST B  -  `GET /api/v1/groups/<uuid>/leaderboard/?period=weekly` (authenticated)

Ab ek authenticated, read-heavy request. Yeh dikhata hai ki cache, DB, object-permission, aur ORM annotation kaise jud te hain.

```http
GET /api/v1/groups/3f9a.../leaderboard/?period=weekly HTTP/1.1
Host: api.grindmate.app
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

##### 2.1 Trace diagram

```
 REQUEST B: GET /api/v1/groups/<uuid>/leaderboard/?period=weekly

  gunicorn → WSGI → [ MIDDLEWARE onion: same 9 layers ] → URL resolver
 │
 "api/v1/" → "groups/" → "<uuid:public_id>/leaderboard/" -----┘
 │
 ▼
 ┌-------------------- DRF LeaderboardView.dispatch() --------------------┐
 │ │
 │  initial(request): │
 │  ┌------------------------------------------------------------------┐  │
 │  │ 1. AUTH: JWTAuthentication │  │
 │  │ - "Authorization: Bearer <jwt>" header parse │  │
 │  │ - signature verify (HMAC, SECRET_KEY) + exp check │  │
 │  │ - payload se user_id → 1 DB query → request.user = <User> │  │ -- DB
 │  │ (expired/invalid → 401 yahin, view tak pahuncha hi nahi) │  │
 │  └------------------------------------------------------------------┘  │
 │  ┌------------------------------------------------------------------┐  │
 │  │ 2. PERMISSION (class-level, has_permission): │  │
 │  │ IsAuthenticated  → request.user.is_authenticated == True? │  │
 │  └------------------------------------------------------------------┘  │
 │  ┌------------------------------------------------------------------┐  │
 │  │ 3. THROTTLE: UserRateThrottle → 1000/hour for this user_id │  │
 │  └------------------------------------------------------------------┘  │
 │ │
 │  get(request, public_id): │
 │  ┌------------------------------------------------------------------┐  │
 │  │ group = get_object_or_404(Group, public_id=...) -----------------┼--┼- DB
 │  │ self.check_object_permissions(request, group) │  │
 │  │ → IsGroupMember.has_object_permission(req, view, group) │  │
 │  │ → group.has_member(user)  → .exists() ----------------┼--┼- DB
 │  │ (not member → 403 yahin) │  │
 │  │ period = "weekly"  (query_params se, validate) │  │
 │  │ │  │
 │  │ rows = compute_leaderboard(group, "weekly") │  │
 │  │ ┌---------------------------------------------------------┐ │  │
 │  │ │ key = "leaderboard:<uuid>:weekly" │ │  │
 │  │ │ hit = cache.get(key)  ------------------------------------┼----┼--┼- REDIS
 │  │ │ HIT  → return cached rows  (DB ko HAATH NAHI lagta!) │ │  │
 │  │ │ MISS → _compute_uncached(group, "weekly") │ │  │
 │  │ │ - 1 annotated query (counts+score)  -----------┼----┼--┼- DB
 │  │ │ - 1 distinct-dates query (streaks) ------------┼----┼--┼- DB
 │  │ │ cache.set(key, rows, 60s)  ----------------------┼----┼--┼- REDIS
 │  │ └---------------------------------------------------------┘ │  │
 │  │ │  │
 │  │ LeaderboardRowSerializer([asdict(r) ...], many=True).data │  │
 │  │ return Response({"period": "weekly", "rows": [...]}) │  │
 │  └------------------------------------------------------------------┘  │
 └--------------------------------------------------------------------------┘
 │
 ▼  200 OK JSON  ← middleware (bottom→top) ← gunicorn
```

##### 2.2 JWTAuthentication  -  Bearer token decode

Ab `Authorization: Bearer <jwt>` header hai. `JWTAuthentication` (DRF default ka pehla authenticator, `base.py:137`) chalta hai:

- Header parse: `AUTH_HEADER_TYPES = ("Bearer",)` (`base.py:168`)  -  toh `Bearer ` prefix expect karta hai. `Token ` ya kuch aur prefix hua toh ignore (`None` return, agla authenticator try).
- Raw token nikaal kar `AccessToken(raw_token)` banata hai  -  yeh **signature verify** karta hai (`HMAC-SHA256` with `SECRET_KEY`) aur `exp` claim check karta hai. Signature tampered ya token expired → `InvalidToken` → DRF `401`.
- Valid hua toh payload se `user_id` claim padhta hai (`USER_ID_CLAIM`, `base.py:170`) aur **ek DB query** `User.objects.get(id=user_id)` chalata hai. Yeh `request.user` set kar deta hai (real `User` instance, `AnonymousUser` nahi).

**Stateless ka matlab:** Server ko har request pe yaad rakhne ki zaroorat nahi ki "kaun logged in hai"  -  token khud proof hai. Sirf user ko hydrate karne ke liye ek DB lookup. (Refresh tokens *stateful* hain  -  woh DB mein blacklist ho sakte hain; access tokens nahi.)

##### 2.3 Permissions  -  do level: class-level + object-level

Yeh DRF ka subtle but important part hai. Do alag permission checks hote hain:

```python
# apps/groups/views.py:163-171
class LeaderboardView(APIView):
 def get_permissions(self):
 return [permissions.IsAuthenticated(), IsGroupMember()]

 def get(self, request, public_id):
 group = get_object_or_404(Group, public_id=public_id)
 self.check_object_permissions(request, group)
 ...
```

- **Class-level (`has_permission`)**  -  `initial()` mein automatically chalta hai. `IsAuthenticated.has_permission()` check karta hai user logged-in hai ya nahi. `IsGroupMember.has_permission()` define hi nahi (`permissions.py:10-16` mein sirf `has_object_permission` hai), toh `BasePermission` ka default `has_permission` → `True`. Matlab is stage pe `IsGroupMember` kuch nahi rokta.
- **Object-level (`has_object_permission`)**  -  yeh **automatically nahi** chalta plain `APIView` mein. View ko **khud** `self.check_object_permissions(request, obj)` call karna padta hai. Isiliye `views.py:171` mein explicitly call kiya gaya hai. Yeh har permission class ka `has_object_permission(request, view, group)` chalata hai:

```python
# apps/groups/permissions.py:10-16
class IsGroupMember(permissions.BasePermission):
 message = "You are not a member of this group."
 def has_object_permission(self, request, view, obj: Group) -> bool:
 return obj.has_member(request.user)
```

`has_member` (`apps/groups/models.py:48-49`):

```python
def has_member(self, user) -> bool:
 return self.memberships.filter(user=user).exists()
```

Member nahi toh `False` → DRF `403 Forbidden` with `"You are not a member of this group."` raise.

**Common gotcha:** Generic views (`RetrieveAPIView` etc.) jab `get_object()` use karte hain toh woh **andar se** `check_object_permissions` call kar dete hain. Par `LeaderboardView` ek plain `APIView` hai jisme hum manually `get_object_or_404` karte hain  -  isiliye object permission bhi **manually** call karni padti hai. Yeh bhool jaana ek classic security bug hai: ek non-member doosre group ka leaderboard dekh leta agar yeh line miss hoti.

Notice `GroupDetailView` (`views.py:69-72`) ek aur pattern dikhata hai  -  method ke hisaab se permission swap:

```python
def get_permissions(self):
 if self.request.method in permissions.SAFE_METHODS: # GET/HEAD/OPTIONS
 return [permissions.IsAuthenticated(), IsGroupMember()]
 return [permissions.IsAuthenticated(), IsGroupAdmin()] # PATCH/DELETE
```

Read karne ko member kaafi, edit/delete ko admin chahiye. Yeh runtime pe permission decide karne ka idiomatic tareeka hai.

##### 2.4 Cache aur DB path  -  yahin asli "deep" baat hai

`compute_leaderboard` (`apps/groups/leaderboard.py:72-81`):

```python
def compute_leaderboard(group, period="weekly"):
 key = _cache_key(str(group.public_id), period) # "leaderboard:<uuid>:weekly"
 hit = cache.get(key)
 if hit is not None:
 return hit # CACHE HIT  -  DB chhua hi nahi
 rows = _compute_uncached(group, period) # CACHE MISS  -  DB pe jao
 cache.set(key, rows, timeout=LEADERBOARD_CACHE_TTL)  # 60s
 return rows
```

**Cache kahan baithta hai:** `CACHES["default"]` Redis hai (`base.py:194-200`). `cache.get(key)` Redis se ek pickled Python object (list of `LeaderboardRow` dataclasses) wapas laata hai. Hit hua toh poora `_compute_uncached`  -  do DB queries  -  **bypass** ho jaata hai. Yahi free-tier deployment pe DB load bachata hai.

**Cache key design:** `f"leaderboard:{group_public_id}:{period}"` (`leaderboard.py:62-63`). Per-group, per-period. Toh `daily`/`weekly`/`all-time` ke alag entries.

**Invalidation:** TTL sirf 60s (`leaderboard.py:26`) hai  -  leaderboard fast-moving data hai. Par TTL ke bharose nahi baithe; jab kisi member ka LeetCode sync naya `SubmissionLog` banata hai, ek signal cache phaad deta hai (`apps/leetcode/signals.py:31` → `invalidate_group_leaderboard(public_id)`), jo teeno periods ki keys delete karta hai (`leaderboard.py:66-69`). Isse **stale leaderboard** ka window minimize hota hai bina har request pe DB hit kiye. Yeh "TTL + event-based invalidation" dono saath  -  ek mature caching pattern hai.

**Cache MISS pe  -  `_compute_uncached` (`leaderboard.py:84-188`):** Yeh do queries chalata hai (N+1 se bachte hue):

1. **Annotated members query (`leaderboard.py:100-150`)**  -  ek hi SQL mein har member ka total/easy/medium/hard count aur weighted score nikaalta hai. Key ORM concepts:
 - `group.memberships.select_related("user")`  -  `JOIN` user table, taaki har member ka `m.user.username` access karne pe alag query na chale (N+1 avoid).
 - `Count("user__submissions", filter=scope, distinct=True)`  -  yeh SQL `COUNT(DISTINCT ...) FILTER (WHERE ...)` mein translate hota hai. `scope` ek reusable `Q` object hai (`leaderboard.py:90-96`) jo period window (`solved_at >= start AND < end`) define karta hai.
 - `score` ek `Sum(Case(When(...)))` hai  -  difficulty ko 1/3/5 weight (`leaderboard.py:29`) deta hai SQL `CASE WHEN` se. Matlab scoring DB mein hoti hai, Python mein nahi  -  fast aur ek query.
 - `Coalesce(..., Value(0))`  -  agar member ne kuch solve nahi kiya toto `NULL` ke bajaye `0`. Warna `None` Python tak aata aur ranking gadbad hoti.
 - `.order_by("-score", "-total", "user__username")`  -  ranking yahin SQL `ORDER BY` se ho jaati.

2. **Distinct-dates query (`leaderboard.py:155-161`)**  -  streaks ke liye. Har user ki distinct solve-dates ek hi query mein laata hai (`TruncDate`, `values_list("user_id", "d").distinct()`), phir Python mein `compute_streaks()` (`apps/leetcode/managers.py`) se current/longest streak nikaalta hai. **Design decision:** streak ek window-function/recursive logic hai jo SQL mein likhna painful aur DB-portability todne wala hota  -  isiliye counts SQL mein, streak Python mein. Hybrid approach, comment bhi yahi bolta hai (`leaderboard.py:5-8`).

**Lazy queryset gotcha:** Dhyaan de `members_qs` (`leaderboard.py:100`) ek queryset hai  -  define karte time DB pe **kuch nahi** chalta. Query actually tab fire hoti hai jab `user_ids = [m.user_id for m in members_qs]` (`leaderboard.py:152`) iterate karta hai, aur dobara `for rank, m in enumerate(members_qs, ...)` (`leaderboard.py:168`) pe  -  par Django queryset apna result **cache** kar leta hai pehle evaluation ke baad, toh dusri baar DB hit nahi hota. Yeh samajhna zaroori hai warna log "double query" ka dar pe `list()` zabardasti laga dete hain.

##### 2.5 Serializer  -  shape dena

```python
# apps/groups/views.py:177-179
rows = compute_leaderboard(group, period)
data = LeaderboardRowSerializer([asdict(r) for r in rows], many=True).data
return Response({"period": period, "rows": data})
```

`rows` `LeaderboardRow` dataclass instances ki list hai. `asdict(r)` har dataclass ko plain dict mein convert karta hai, phir `LeaderboardRowSerializer(..., many=True)` use kiya gaya **output ko shape/validate** karne ke liye. Yahan serializer ka kaam input validation nahi (woh `period` check view mein hua), balki output ka consistent JSON contract dena hai  -  kaunse fields, kis order/type mein. `Response(...)` DRF ka renderer (`JSONRenderer`) use karke dict ko JSON bytes mein badal deta hai, content negotiation ke baad.

---

#### 3. 401 + Token Refresh flow

Access token sirf 15 min jeeta hai (`base.py:160-162`). 15 min baad agar React app `GET /leaderboard/` maarta hai purane access token se, `JWTAuthentication` (section 2.2) `exp` check fail karta hai → **`401 Unauthorized`**  -  view tak pahuncha hi nahi.

**Frontend side (sirf reference ke liye):** React ka axios interceptor `401` dekh kar `POST /api/v1/auth/token/refresh/` maarta hai refresh token ke saath, naya access token leta hai, aur original failed request ko retry karta hai. Yeh transparent hota hai  -  user ko pata bhi nahi chalta.

**Backend side  -  yahan focus.** Route `apps/users/urls.py:14`:

```python
path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
```

Yeh simplejwt ka built-in `TokenRefreshView` hai. Request body `{"refresh": "<refresh_jwt>"}`. Iska serializer:

1. Refresh token verify karta hai (signature + `exp`). 7-din se purana ya invalid → `401`.
2. **Blacklist check**  -  kyunki humne `token_blacklist` app install kiya hai (`base.py:42`), refresh token DB ki blacklist table mein check hota hai. Agar pehle se blacklisted (logout ya rotate ho chuka) → reject.
3. Naya **access token** mint karke return.

Hamare config mein do critical flags (`base.py:166-167`):

```python
"ROTATE_REFRESH_TOKENS": True,
"BLACKLIST_AFTER_ROTATION": True,
```

- `ROTATE_REFRESH_TOKENS`  -  har refresh pe ek **naya refresh token bhi** milta hai (sirf access nahi). Response mein `{access, refresh}` dono aate hain.
- `BLACKLIST_AFTER_ROTATION`  -  purana refresh token rotate hone ke baad **DB blacklist** mein daal diya jaata hai. Iska security benefit: agar koi attacker purana refresh token chura le, woh ek baar use hote hi blacklist ho jaata; jab attacker dobara use kare toh reject. Yeh **token reuse detection** ka foundation hai.

**Logout** (`apps/users/views.py:54-68`) bhi isi blacklist machinery pe chalta hai  -  `RefreshToken(refresh).blacklist()` token ko DB blacklist table mein daal deta hai, taaki logout ke baad woh refresh token kabhi naya access na de.

**Yaad rakh:** access token *stateless* hai  -  usko "revoke" nahi kar sakte expiry se pehle (isiliye 15-min short rakha). Refresh token *stateful* hai  -  DB blacklist se revoke ho sakta hai. Yeh do alag philosophies ek system mein balance kiya gaya hai.

```
 401 + REFRESH ka backend dance

 GET /leaderboard/  (access token 15 min purana)
 │
 ▼  JWTAuthentication: exp fail → 401  (view tak nahi pahuncha)
 │
 [frontend interceptor]  POST /auth/token/refresh/  {refresh}
 │
 ▼  TokenRefreshView:
 - refresh verify (sig + exp)
 - DB blacklist check  ---- blacklisted? → 401
 - naya access mint
 - ROTATE: naya refresh bhi mint
 - BLACKLIST_AFTER_ROTATION: purana refresh → DB blacklist
 │
 ▼  200 {access, refresh}  (frontend retry original request)
```

---

#### 4. Mental Model  -  har layer ka ek-line role

Jab bhi kisi request ke baare mein soch, yeh table dimaag mein rakh  -  yahi poore backend ka skeleton hai:

| Layer | Role (ek line) | GrindMate file |
|---|---|---|
| **gunicorn / WSGI** | TCP socket + raw HTTP ko Python `environ` dict banata; process workers | `grindmate/wsgi.py`, `WSGI_APPLICATION` |
| **Middleware** | Cross-cutting concerns  -  security, CORS, session, auth-hint, CSRF. Request neeche, response upar (onion) | `base.py:58-68` |
| **URLs** | Routing  -  URL string → kaunsi view. Prefix-by-prefix include chain | `grindmate/urls.py`, `apps/*/urls.py` |
| **Views (controller)** | Orchestration  -  gatekeepers chalao, service/ORM call karo, Response banao | `apps/*/views.py` |
| **Auth / Permission / Throttle (gatekeepers)** | Kaun ho? (auth) Andar aa sakte ho? (permission) Kitni baar? (throttle) | `JWTAuthentication`, `IsGroupMember`, `AnonRateThrottle` |
| **Serializers (validation / shape)** | Input validate karo, output ka JSON contract do | `apps/*/serializers.py` |
| **Service layer** | Heavy business logic views se alag  -  testable, cacheable | `apps/groups/leaderboard.py` |
| **Models / ORM (data)** | Lazy querysets → SQL. select_related/annotate se N+1 aur multi-query se bacho | `apps/groups/models.py`, leaderboard query |
| **Cache (Redis)** | Mehnga compute bachao; TTL + event invalidation | `CACHES`, `compute_leaderboard` |
| **Signals (side-effects)** | Decoupled reactions  -  submission save → leaderboard cache invalidate | `apps/leetcode/signals.py` |

Ek line mein poora flow: **gunicorn raw request laata hai → middleware onion se guzarti hai → URL resolver view dhoondta hai → view ke gatekeepers (auth/permission/throttle) check karte hain → serializer validate karta hai / service+ORM data laata hai (cache check ke baad) → Response banti hai → wapas middleware onion (ulta) se guzar kar JSON client ko milta hai.**

---

#### Common Galtiyan / Gotchas (consolidated)

- **`AllowAny` bhoolna login/register pe**  -  global default `IsAuthenticated` (`base.py:140`) hai, toh anonymous endpoints pe explicitly `AllowAny` na lagaya toh 401 milega aur user kabhi login hi nahi kar paayega.
- **Plain `APIView` mein `check_object_permissions` miss karna**  -  generic views auto-call karte hain, plain `APIView` nahi. Miss kiya toh object-level security hole. `LeaderboardView` ne `views.py:171` pe sahi se call kiya.
- **Middleware order ulta-pulta**  -  CORS ko CommonMiddleware se upar rakhna padta; Session ko Auth se upar. Galat order pe CORS errors ya `request.user` resolve na hona.
- **Queryset double-query ka dar**  -  Django queryset pehle evaluation pe result cache kar leta; dubara iterate pe DB hit nahi. Zabardasti `list()` lagana zaroori nahi (jab tak fresh query na chahiye).
- **Access token revoke karne ki koshish**  -  woh stateless hai, expiry tak valid rahega. Revocation refresh token pe hota hai (blacklist). Isiliye access lifetime short rakhte hain.

---

#### Interview Questions + short jawab

1. **Q: Django middleware "request neeche, response upar" ka kya matlab hai?**
 A: Middleware ek onion hai. `__call__` mein `get_response()` se pehle wala code request pe top-to-bottom chalta hai; uske baad wala code response pe bottom-to-top. Ek hi list, par do directions.

2. **Q: DRF mein `has_permission` aur `has_object_permission` mein farak?**
 A: `has_permission` class-level, har request pe auto chalta (`initial()` mein). `has_object_permission` ek specific object pe  -  generic views auto-call karte hain par plain `APIView` mein khud `check_object_permissions()` call karna padta hai.

3. **Q: Login endpoint pe CSRF middleware kyun block nahi karta?**
 A: DRF ki `APIView` middleware-level pe `csrf_exempt` hai; CSRF enforcement DRF ke andar sirf `SessionAuthentication` ke liye hota hai. JWT-based auth pe CSRF check skip hota hai.

4. **Q: Access token aur refresh token mein conceptual farak?**
 A: Access stateless + short-lived (15 min), har API call pe bhejte hain, revoke nahi kar sakte. Refresh stateful + long-lived (7 din), DB blacklist se revoke ho sakta, sirf naya access lene ke liye use hota.

5. **Q: `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` ka security faayda?**
 A: Har refresh pe naya refresh token milta aur purana blacklist ho jaata. Agar chura hua purana token dobara use ho, reject  -  yeh token reuse detect karne deta hai.

6. **Q: Leaderboard response mein DB kab hit hota hai aur kab nahi?**
 A: Pehle Redis cache (`leaderboard:<uuid>:<period>`) check hota. Hit → DB bilkul nahi. Miss → do queries (annotated counts/score + distinct dates), phir 60s ke liye cache.

7. **Q: Leaderboard cache stale hone se kaise bachte ho?**
 A: TTL 60s + event-based invalidation dono. Naye `SubmissionLog` pe signal `invalidate_group_leaderboard` teeno period keys delete kar deta hai.

8. **Q: Score calculation Python mein kyun nahi, SQL mein kyun?**
 A: `Sum(Case(When(difficulty=..., then=Value(weight))))` se DB hi ek query mein weighted score nikaal deta  -  fast, no N+1. Sirf streak (jo SQL mein painful hai) Python mein nikalte hain.

---

#### Khud try kar (exercises)

1. **Middleware order tod ke dekh:** `CorsMiddleware` ko list mein neeche `CommonMiddleware` ke baad shift kar, dev server chala, React app se login maar. Browser console mein CORS error reproduce kar  -  phir wapas sahi karke samajh ki order kyun maayne rakhta tha.

2. **Object-permission hole simulate kar:** `LeaderboardView.get` se `self.check_object_permissions(request, group)` (`views.py:171`) comment out kar de. Do users, do groups bana. User A ke token se User B ke group ka leaderboard maar  -  ab woh data dikhega jo nahi dikhna chahiye. Yeh dekh kar samajh ki line kyun load-bearing hai. (Phir wapas uncomment kar.)

3. **Cache hit/miss observe kar:** `compute_leaderboard` mein `cache.get(key)` ke aas-paas do `logger.info("cache HIT/MISS ...")` lines daal. Ek hi leaderboard endpoint do baar jaldi-jaldi maar  -  pehli MISS, doosri HIT dikhni chahiye. Phir ek naya `SubmissionLog` create kar (shell se) aur dobara maar  -  signal invalidation ke kaaran phir MISS aana chahiye.


---


## 8. Study Roadmap, Glossary & Interview Prep Bank

Dekh bhai, ye chapter thoda alag hai. Baaki chapters tujhe *concept* sikhaate hain  -  ye chapter tujhe sikhaata hai ki **un chapters ko padhna kis order me hai**, **codebase me haath kaise ganda karna hai**, aur **interview me kya poocha jaayega**. Isko apna "control room" samajh. Jab bhi confuse ho, yahan wapas aa.

GrindMate ek chhota sa real project hai  -  friend-group LeetCode tracker. Iska backend Django 5 + DRF hai, teen apps hain: `users` (custom auth), `leetcode` (GraphQL sync), `groups` (leaderboard). Yahi teen cheezein agar tu theek se samajh gaya, toh tera fresher-level backend interview clear hai.

---

#### 1. Kis order me padho (Learning Roadmap)

Tu seedha leaderboard ka annotated query padhega toh sar ghoom jaayega. Foundation se shuru kar. Har step pe maine likha hai *kya focus karna hai* aur *kitna time* (assume tu roz 2-3 ghante de raha hai).

| # | Chapter / Topic | Kya focus karna hai | Roughly time |
|---|------------------|---------------------|--------------|
| 1 | **Python/Django Foundations** | Request → response cycle, MVT (Model-View-Template, par yahan Template ki jagah JSON), app vs project ka farak. `manage.py` kya karta hai. | 1 din |
| 2 | **Settings split** (`grindmate/settings/base.py`, `development.py`, `production.py`, `test.py`) | `base.py` me sab common, baaki environment-specific. `INSTALLED_APPS`, `MIDDLEWARE` ka order, `django-environ` se env variables. **Kyun split kiya**  -  dev me SQLite + LocMem, prod me Postgres + Redis. | 1 din |
| 3 | **Users / Auth** (`apps/users/models.py`, `managers.py`, JWT settings) | Custom `User` model (`AbstractBaseUser`), `email` as `USERNAME_FIELD`, custom `UserManager`, password hashing, JWT (access + refresh), token rotation/blacklist, throttling. | 2 din |
| 4 | **LeetCode services + sync** (`apps/leetcode/services.py`, `sync.py`, `models.py`) | Service layer kyun alag, GraphQL client, retries, `defer_meta` ka design, `SyncResult` DTO (dataclass), `get_or_create` idempotency, `transaction.atomic`. | 3 din (sabse meaty) |
| 5 | **Groups / ORM deep dive** (`apps/groups/leaderboard.py`, `models.py`, `managers.py`) | Annotated single-query leaderboard, `Coalesce`/`Count`/`Sum`/`Case`/`When`, `select_related` vs `prefetch_related`, N+1, custom manager/queryset, through-model M2M, `select_for_update` race condition. | 3 din |
| 6 | **Celery + Tests** (`settings` Celery block, data migration, `tests/`) | Celery broker/worker/beat, dev me eager vs prod me GitHub Actions cron, data migration se schedule register, pytest + factory_boy + `responses` se external API mock. | 2 din |
| 7 | **Request lifecycle (full picture)** (`grindmate/urls.py`, middleware, DRF view → serializer → response) | Ek request `/api/v1/groups/<id>/leaderboard/` se kaise travel karti hai: middleware → URL resolve → permission → view → service → serializer → JSON. Sab jod ke ek mental movie bana. | 1 din |

> **Senior advice**: Step 4 aur 5 par sabse zyada ruk. Interview me 70% questions yahin se aate hain  -  "leaderboard ek query me kaise", "N+1 kya hai", "service layer kyun". Inko ratna mat, *samajhna*.

---

#### 2. Hands-on milestones (sirf padho mat, karo)

Padhke kuch yaad nahi rehta. Code chhedo, todo, fix karo  -  tab dimaag me chipakta hai. Ye 8 milestones cross karo, ek-ek karke.

**Milestone 1  -  Server chala aur health check maar.**
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1 # PowerShell pe
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Browser me `http://localhost:8000/health/` aur `/admin/` khol. Admin me apne `User`, `Group`, `SubmissionLog` dikhne chahiye. **Goal**: pura stack boot ho raha hai, ye confirm.

**Milestone 2  -  Django shell me ORM query maar.**
```bash
python manage.py shell
```
```python
from apps.leetcode.models import SubmissionLog
# Custom manager methods chala  -  README me ye advertise kiye gaye hain
SubmissionLog.objects.this_week().count()
SubmissionLog.objects.by_difficulty() # {difficulty: count} dict
```
**Goal**: `managers.py` ka custom queryset live dekh. Dhyaan de  -  `.count()` lagaya tab DB pe query gayi (queryset *lazy* hota hai).

**Milestone 3  -  Naya field add kar + migration bana.**
`apps/users/models.py` ke `User` me ek field daal, e.g.:
```python
bio = models.CharField(max_length=160, blank=True)
```
Phir:
```bash
python manage.py makemigrations users
python manage.py migrate
```
`apps/users/migrations/` me naya file khol kar dekh  -  Django ne kya generate kiya. **Goal**: schema change → migration file → DB. (Baad me revert kar dena.)

**Milestone 4  -  Naya endpoint likh.**
`apps/users/views.py` me ek `MeStatsView` add kar jo logged-in user ka `total_solved` aur `current_streak` return kare. Hint  -  `SubmissionLog.objects.distinct_solved_dates(user)` + `compute_streaks(...)` use kar (`apps/leetcode/managers.py` me already hai). URL `grindmate/urls.py` / app urls me wire kar. **Goal**: view → service function → serializer → JSON ka pura flow khud likha.

**Milestone 5  -  Ek test likh aur chala.**
`apps/leetcode/tests/test_managers.py` dekh, phir `compute_streaks` ke liye ek naya test case add kar (e.g. 3 consecutive din ka streak). `factory_boy` factories `apps/*/factories.py` me hain  -  unse data bana.
```bash
pytest apps/leetcode/tests/test_managers.py -q
```
**Goal**: factory se object banana + assertion likhna.

**Milestone 6  -  Jaan-boojh ke todo, traceback padho.**
`apps/groups/leaderboard.py` me `EASY_WEIGHT, MEDIUM_WEIGHT, HARD_WEIGHT = 1, 3, 5` ko `= 1, 3` kar de (ek value hata). `pytest` chala. `ValueError: not enough values to unpack` dekh  -  traceback ke **last frame** se upar padh, file:line dhoondh. **Goal**: error ghabraana band, traceback bottom-up padhna seekh. (Wapas theek kar.)

**Milestone 7  -  Leaderboard query ka SQL dekh.**
```python
# shell me
from apps.groups.models import Group
from apps.groups.leaderboard import _compute_uncached
g = Group.objects.first()
# Query banao par print karne se pehle SQL nikaalo:
from django.db import connection, reset_queries
from django.conf import settings; settings.DEBUG = True
reset_queries()
_compute_uncached(g, "weekly")
print(len(connection.queries)) # kitni queries chali?
for q in connection.queries: print(q["sql"][:200])
```
**Goal**: apni aankhon se dekh ki leaderboard ~2 queries me ban raha hai (members annotated + distinct dates), N queries me nahi. **Yahi project ka crown jewel hai.**

**Milestone 8  -  Manual sync command chala (mock ke saath).**
Real LeetCode hit karne se pehle `apps/leetcode/tests/test_services.py` dekh  -  `responses` library se GraphQL endpoint mock kiya gaya hai. Ek test add kar jo `sync_account` ko mocked response ke saath chalaye aur `SubmissionLog` rows banne ki assert kare. **Goal**: external API ko bina internet ke test karna.

---

#### 3. GLOSSARY (40 terms  -  ek line Hinglish me)

| Term | Hinglish definition |
|------|---------------------|
| **QuerySet** | DB query ka *lazy* representation  -  jab tak iterate/`.count()`/`list()` na karo, SQL fire hi nahi hoti. |
| **Annotation** | Har row ke saath ek computed extra column jod dena (e.g. `member_count=Count(...)`), DB me hi calculate hoke aata hai. |
| **Aggregation** | Poore queryset pe ek single summary value nikaalna (e.g. total count, sum)  -  `.aggregate()`. Annotation per-row, aggregation per-queryset. |
| **F expression** | DB column ko Python me laaye bina uspe operate karna  -  `F("use_count") + 1` race-condition-safe increment deta hai (`groups/models.py` me `consume()`). |
| **Coalesce** | "Pehla non-NULL le"  -  `Coalesce(Count(...), Value(0))` matlab agar count NULL ho toh 0 de. Leaderboard me har member ko 0 default mile. |
| **Case / When** | SQL ka if-else  -  `Case(When(difficulty="easy", then=Value(1)), ...)` se difficulty ko points me convert kiya score ke liye. |
| **Serializer** | Model/dataclass ↔ JSON ka translator + validator. `ModelSerializer` model se fields infer karta hai; plain `Serializer` (jaise `LeaderboardRowSerializer`) manually fields likhne padte hain. |
| **Middleware** | Har request/response ke beech ki processing pipeline ki layer  -  security, CORS, session, auth sab middleware hain (`settings/base.py` ka `MIDDLEWARE` list). |
| **JWT** | JSON Web Token  -  server-side session store kiye bina, signed token me user identity carry hoti hai. Stateless auth. |
| **Access token** | Short-lived JWT (yahan 15 min) jo har API call ke `Authorization: Bearer` header me jaata hai. |
| **Refresh token** | Long-lived token (yahan 7 din) jisse naya access token milta hai bina dobara login kiye. |
| **Token rotation** | Har refresh pe naya refresh token milta hai aur purana blacklist ho jaata hai (`ROTATE_REFRESH_TOKENS=True`)  -  chori hone pe damage kam. |
| **Throttle** | Rate limit  -  ek user/IP ek ghante me kitni request kar sakta hai (`register: 10/hour`). Brute-force/spam rokne ko. |
| **Signal** | Django ka event hook  -  "jab X save ho, ye function chala". GrindMate me `post_save` on `SubmissionLog` se leaderboard cache invalidate hota hai. |
| **Migration** | Model changes ko DB schema changes me badalne wali versioned file  -  `makemigrations` banata, `migrate` apply karta. |
| **Data migration** | Schema nahi, *data* badalne wali migration  -  GrindMate me `0002_register_sync_schedule` Celery beat schedule DB me daalti hai deploy pe. |
| **Manager** | Model ka query gateway  -  `Model.objects` ek manager hai. Custom manager se `.this_week()` jaise reusable queries milte hain. |
| **QuerySet method (custom)** | Manager pe attach reusable filter  -  chainable, e.g. `.for_user(u).in_range(a, b)`. |
| **dataclass** | `@dataclass` se boilerplate-free Python class jisme sirf data fields hon  -  `SyncResult`, `LeaderboardRow` isi se bane. |
| **DTO** | Data Transfer Object  -  layers ke beech data le jaane wala simple structure. `SyncResult` service se command tak data carry karta hai. |
| **Idempotent** | Ek operation chahe 1 baar chale ya 5 baar, result same  -  `get_or_create` se duplicate sync pe duplicate `SubmissionLog` nahi banta. |
| **Race condition** | Do request ek saath same resource chhede aur galat result aaye  -  invite join me `select_for_update` se rok lagayi. |
| **select_for_update** | Row pe DB-level lock le leta hai transaction ke andar, taaki doosri concurrent request usko padh/likh na sake jab tak tu commit na kare. |
| **N+1 problem** | 1 query se N parent laaye, phir har ek ke liye alag query (kul N+1)  -  slow. Leaderboard `select_related("user")` se ise avoid karta. |
| **select_related** | ForeignKey/OneToOne ko ek SQL JOIN me saath le aata  -  single-valued relations ke liye. |
| **prefetch_related** | M2M / reverse-FK ko alag query me laake Python me jod deta  -  multi-valued relations ke liye (`groups/views.py` me `Prefetch`). |
| **Prefetch (object)** | Customized prefetch  -  sirf current user ki membership prefetch karo, sab nahi (role dikhane ke liye, extra query bachi). |
| **atomic transaction** | `transaction.atomic()` block  -  andar sab kuch ek saath commit ya kuch bhi nahi (all-or-nothing). Sync me half-written data nahi bachta. |
| **get_or_create** | Object dhoondh, na mile toh bana de  -  atomic, idempotent. Sync aur join dono me use hua. |
| **update_or_create** | Mile toh update, na mile toh bana  -  `upsert_problem` me problem metadata refresh karne ko. |
| **TextChoices** | Enum-jaisa Django class for choice fields  -  `SyncStatus.OK`, `Difficulty.EASY`. Strings hardcode karne se bachta. |
| **decorator** | Function ko wrap karke behavior add karna  -  `@receiver(post_save, ...)`, `@transaction.atomic`, `@dataclass`. |
| **context manager** | `with ...:` block jo resource setup/cleanup handle kare  -  `with transaction.atomic():`. |
| **Celery broker** | Task queue ka message bus (Redis)  -  jahan "ye task chalao" messages padte hain. |
| **Celery worker** | Background process jo broker se task uthata aur chalata hai. |
| **Celery beat** | Scheduler jo cron-jaise periodic tasks ko time pe broker me daalta hai. |
| **Cache invalidation** | Stale cached data ko delete karna jab underlying data badle  -  naya solve aaya toh leaderboard cache `delete`. |
| **TTL (time-to-live)** | Cache entry kitni der zinda rahegi  -  leaderboard `60` second, default cache `300`. |
| **CORS** | Cross-Origin Resource Sharing  -  browser ko batata ki kaunse frontend origins (Vercel URL) API hit kar sakte. |
| **CSRF** | Cross-Site Request Forgery protection  -  cookie-based forms ke liye. JWT (header-based) hone se API pe iska zyada relevance nahi. |
| **Hashing / salt** | Password ko irreversibly scramble karna + random salt jodna  -  `set_password()` PBKDF2 use karta, plain text kabhi store nahi hota. |
| **WhiteNoise** | Django ko apni static files khud serve karne deta bina alag CDN/nginx ke (prod me). |

---

#### 4. INTERVIEW PREP BANK (GrindMate-specific, topic-wise)

##### A. Django basics

**Q1. Project aur app me farak?**
Project (`grindmate/`) pura config + settings + URLs hota hai; app (`apps/users`, `apps/leetcode`, `apps/groups`) ek reusable feature module. Ek project me kai apps. GrindMate me teen domain apps hain.

**Q2. Settings ko 4 files me kyun split kiya?**
`base.py` me common, phir `development/production/test.py` inherit karte. Dev me SQLite + LocMem cache + console email, prod me Postgres + Redis + SMTP. Isse same code alag environment me safely chalta, aur secrets env vars se aate (`django-environ`)  -  git me nahi.

**Q3. `MIDDLEWARE` ka order matter karta hai?**
Haan. Request top-to-bottom, response bottom-to-top guzarti. `SecurityMiddleware` pehle, `WhiteNoise` static ke liye, `CorsMiddleware` upar taaki CORS headers session/auth se pehle lag jaayein.

**Q4. `manage.py migrate` aur `makemigrations` me farak?**
`makemigrations` model change ko padhke migration *file* banata (sirf instructions). `migrate` un files ko *DB pe apply* karta. Do alag step taaki migration review/version-control ho sake.

##### B. DRF

**Q5. `ModelSerializer` vs plain `Serializer` kab?**
`ModelSerializer` (jaise `GroupSerializer`) DB model se fields auto-infer karta. Plain `Serializer` (jaise `LeaderboardRowSerializer`) tab jab source ek model nahi balki ek `dataclass`/dict ho  -  leaderboard rows model nahi, computed `LeaderboardRow` hain, isliye fields manually likhe.

**Q6. `SerializerMethodField` kab use kiya aur kyun?**
`GroupSerializer.get_role()` me  -  har group me current user ka role per-request, per-user compute hota hai, model field nahi hai. Method field se request context use karke compute kiya bina extra DB hit ke (prefetched memberships se).

**Q7. Permission classes kaise lagai?**
Default `IsAuthenticated` poore project pe (`settings`). Object-level pe custom `IsGroupMember` / `IsGroupAdmin`  -  `GroupDetailView.get_permissions()` me method ke hisaab se: SAFE_METHODS (GET) pe member chalega, write pe sirf admin.

**Q8. Throttling kahan aur kyun?**
`settings/base.py` me `DEFAULT_THROTTLE_RATES`  -  `register: 10/hour`, `password_reset: 5/hour`. Signup/reset endpoints abuse-prone hain (spam, brute-force), isliye tight limit; normal user `1000/hour`.

##### C. ORM (sabse important)

**Q9. Leaderboard ek hi query me kaise banta hai?**
`groups/leaderboard.py` me `group.memberships.select_related("user")` pe multiple `annotate` lagaye  -  `Coalesce(Count(... filter=scope ...))` har difficulty ka count, aur `Sum(Case(When(...)))` weighted score, sab ek SQL me. Phir streaks ke liye sirf ek aur query (`distinct_solved_dates`) jo Python me process hoti. Kul ~2 query, members ke number se independent.

**Q10. `Coalesce(Count(...), Value(0))` me `Coalesce` kyun chahiye?**
Jis member ne is period me kuch solve nahi kiya, uska `Count` SQL me NULL aata (LEFT JOIN ke wajah se). `Coalesce` usko `0` me badal deta taaki har row me clean integer mile, serializer/Python me `None` handle na karna pade.

**Q11. N+1 problem yahan kahan rokna pada?**
Leaderboard har member ka `user.username`, `public_id` chahiye. Bina `select_related("user")` ke har member pe ek alag user query (N+1) chalti. `select_related` use karke user ko same JOIN me le aaye. Groups list me `prefetch_related(Prefetch("memberships", ...))` se role nikaala.

**Q12. `select_related` vs `prefetch_related`?**
`select_related`  -  FK/OneToOne ke liye, ek SQL JOIN. `prefetch_related`  -  M2M/reverse-FK ke liye, alag query + Python join. Leaderboard me user FK pe `select_related`, group ke members (reverse FK) pe `prefetch_related`.

**Q13. Custom manager/queryset kyun banaya?**
`SubmissionLogManager` + `SubmissionLogQuerySet` me `.this_week()`, `.today()`, `.by_difficulty()`  -  taaki ye queries ek hi jagah, reusable, chainable hon. Views aur Celery tasks ORM noise se free rehte. `Manager.from_queryset(...)` se queryset methods manager pe bhi mil jaate.

**Q14. Race condition invite join me kaise handle ki?**
`JoinByInviteView` me `GroupInvite.objects.select_for_update().get(...)` `transaction.atomic` ke andar  -  invite row pe DB lock lag jaata, do users ek hi single-use invite same waqt na consume kar sakein. `use_count` bhi `F("use_count") + 1` se atomically badhta (`models.py` ka `consume`).

**Q15. `SubmissionLog` pe `UniqueConstraint` kyun?**
`(user, problem, solved_at)` unique  -  agar sync galti se same solve dobara laaye (duplicate sync), DB hi reject kar de. Plus `get_or_create` defensively idempotent rakha. Do-layer safety: app logic + DB constraint.

**Q16. `on_delete` choices kyun alag-alag?**
`SubmissionLog.user` → `CASCADE` (user gaya toh uske solves bhi gaye). `SubmissionLog.problem` → `PROTECT` (problem ko delete na hone do agar usse linked solves hain, data integrity). `Group.owner` → `PROTECT` isliye `User.delete()` me ownership transfer ka custom logic likhna pada.

##### D. Auth / JWT

**Q17. Email-as-username kyun, alag username field bhi kyun rakha?**
`USERNAME_FIELD = "email"`  -  log email yaad rakhte, unique bhi. Par groups/profile me public handle chahiye jo email expose na kare  -  isliye alag `username` (regex-validated). Best of both: email login, username public identity.

**Q18. Custom `User` model `AbstractBaseUser` se kyun, `AbstractUser` se nahi?**
`AbstractUser` me `username` mandatory + Django ka built-in shape. Humein email-primary chahiye tha, isliye `AbstractBaseUser + PermissionsMixin` se scratch se banaya  -  `UserManager` me `create_user`/`create_superuser` khud likhe email ke around.

**Q19. Password kaise store hota, plain text kyun nahi?**
`UserManager._create_user` me `user.set_password(password)`  -  ye PBKDF2 hashing + random salt karta, DB me sirf hash jaata. Plain password kabhi store nahi hota; login pe Django hash compare karta. `AUTH_PASSWORD_VALIDATORS` se strength bhi enforce.

**Q20. Access aur refresh token ka split kyun?**
Access short-lived (15 min)  -  chori ho bhi gaya toh jaldi expire. Refresh long-lived (7 din) par sirf naya access lene ke kaam aata. `ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION`  -  har refresh pe naya refresh, purana blacklist; chori-detection.

**Q21. Frontend 401 pe kya karta?**
Axios interceptor ek baar refresh token se naya access leta aur original request retry karta. Agar refresh bhi fail, user logout. (README "Architecture notes" me documented.)

**Q22. Email verification token single-use kaise?**
`EmailVerificationToken` me `used_at` field + `consume()` method, aur 24h `EXPIRY`. `is_usable()` check karta ki used nahi hua aur expired nahi. Password reset token 1h expiry  -  chhota, kyunki wo password badal sakta (zyada sensitive).

##### E. Architecture / System Design

**Q23. Service layer (`sync.py`, `services.py`) views se alag kyun?**
Business logic (LeetCode pull, persist, aggregate) view se decouple  -  same `sync_account()` ko management command, Celery task aur view sab call kar sakte. View patla rehta (sirf request/response), logic testable rehta bina HTTP ke. "Fat models/services, thin views" principle.

**Q24. `defer_meta=True` ka design kyun?**
Sync ke time har naye problem slug pe LeetCode API hit karna = N extra network calls = slow request. `upsert_problem(defer_meta=True)` placeholder row (`difficulty=""`) banata bina API call ke  -  sync sirf 2 LeetCode calls me bandh ho jaata. Metadata baad me `backfill_problems` cron bhar deta. Latency bounded rakhi.

**Q25. Leaderboard cache + invalidation strategy?**
`compute_leaderboard` Redis (dev me LocMem) me 60s TTL ke saath cache karta, key `(group_public_id, period)`. Naya `SubmissionLog` save hote hi `post_save` signal us user ke saare groups ke cache `delete` kar deta. Toh data fresh bhi rehta aur har page-load pe heavy query nahi chalti.

**Q26. Celery prod me kyun nahi chalaaya, cron kyun?**
Render/Railway free tier pe alag worker dyno nahi mil raha. Toh prod me periodic sync ek HTTP endpoint hai jise GitHub Actions ka cron `CRON_SHARED_SECRET` ke saath hit karta. Dev me asli Celery beat use hota. Same logic, alag trigger  -  cost-zero deploy.

**Q27. Data migration `0002_register_sync_schedule` ka kaam?**
Ye django-celery-beat me periodic task schedule DB me register karti  -  deploy pe automatically, bina admin me manually click kiye. Infra-as-code: naya environment migrate karte hi schedule ready.

**Q28. SMTP timeout kyun set kiya?**
`EMAIL_TIMEOUT = 10`  -  agar Gmail/Resend handshake hang ho jaaye, ek gunicorn worker indefinitely block ho sakta tha. Timeout se worker free rehta, request fail-fast hoti.

**Q29. `public_id` (UUID) aur internal `id` (BigAuto) dono kyun?**
`id` internal PK, fast, FK joins ke liye. `public_id` (UUID) URLs/API me expose hota  -  sequential integer guess/enumerate nahi ho sakta (e.g. `/groups/1/`, `/2/` scrape nahi). Security + clean public API.

##### F. Testing

**Q30. External LeetCode API ko test me kaise handle kiya?**
`responses` library se `leetcode.com/graphql` ko mock kiya jaata (`tests/test_services.py`)  -  real network call nahi hoti, test fast + deterministic + offline. `factory_boy` se test data banate, `freezegun` se time freeze (streak/expiry tests ke liye).

**Q31. `--reuse-db` aur `pytest-django` kyun?**
`pyproject.toml` me `--reuse-db`  -  har test run pe DB dobara create nahi hoti, fast feedback. `DJANGO_SETTINGS_MODULE = grindmate.settings.test` se test-specific settings (eager Celery, fast password hasher waghairah).

**Q32. Eager Celery dev/test me matlab?**
Test/dev me task synchronously, usi process me chalta (broker queue ke bina)  -  `result = task.delay()` turant complete. Isse async behavior test karna simple, bina Redis worker chalaaye.

---

#### 5. Red flags  -  kya AVOID karein (GrindMate ne ye galtiyan consciously nahi ki)

Ye wo classic fresher mistakes hain jinhe ye codebase **jaan-boojh ke** nahi karta. Tu apne code me bhi avoid karna.

1. **Views me business logic thoosna** ❌
 Naya banda poora sync + persist + aggregate seedha view me likh deta. GrindMate ne `sync.py`/`services.py` me service layer banayi  -  view sirf request/response. *Reuse + test + readability sab milta.*

2. **N+1 queries** ❌
 Leaderboard me har member ke liye `member.user.username` access karna = N alag queries. GrindMate `select_related("user")` + `Prefetch` se ek-do query me kaam karta. Hamesha loop se pehle socho "ye DB ko kitni baar hit karega".

3. **Plain text password store karna** ❌
 Kabhi `User(password=raw)` mat karo. `set_password()` use hota jo PBKDF2-hash karta. DB leak ho bhi jaaye toh passwords readable na hon.

4. **External API pe request-time block karna** ❌
 Har naye problem pe LeetCode API hit karoge toh user ki request 30s hang ho jaayegi. `defer_meta` se sync 2 calls me bandh, baaki metadata async backfill. *User-facing latency bounded rakho.*

5. **Secrets git me daalna** ❌
 `SECRET_KEY`, `DATABASE_URL`, `EMAIL_HOST_PASSWORD`, `CRON_SHARED_SECRET` sab `django-environ` se env vars se aate, defaults sirf dev ke liye insecure. `.env` gitignored. *Prod secret kabhi commit mat karo.*

6. **Cache lagaake invalidate bhoolna** ❌
 Sirf `cache.set` lagaake chhod dena = users ko stale leaderboard dikhega. GrindMate `post_save` signal se solve hote hi cache `delete` karta. *Cache lagao toh invalidation bhi socho  -  warna 2 hard problems me se ek tum bana loge.*

7. **Race condition ignore karna** ❌
 Single-use invite pe do log ek saath click karein toh dono join ho sakte. `select_for_update` + atomic transaction + `F()` increment se lock liya. *Concurrent access wale flows me hamesha socho "agar do request ek saath aayein?".*

8. **DB constraint pe bharosa na karna (sirf app-level check)** ❌
 App me duplicate-check + DB `UniqueConstraint` dono. App logic me bug aaye toh DB last line of defense banta. *Defense in depth.*

---

##### Khud try kar (final exercises)

1. **Cache ka asar dekho**: shell me ek group ka `compute_leaderboard(g, "weekly")` do baar chalao, beech me `connection.queries` count check karo. Pehli baar query chali, doosri baar cache se aaya (0 query)  -  confirm karo.
2. **Signal ko trip karo**: ek naya `SubmissionLog` shell me banao us user ke liye jo kisi group me hai, phir us group ke cache key (`leaderboard:<public_id>:weekly`) ko `cache.get` karo  -  `None` aana chahiye (signal ne invalidate kar diya).
3. **Streak logic todo**: `compute_streaks` ko aaj+kal+parso ki dates do, phir ek din ka gap daal ke do  -  `current_streak` aur `longest_streak` kaise badalte, predict karo phir verify karo.
