> **Note: NOT PUBLISHED**

### Preface


<div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 200px;">
    <p style="text-align: justify; line-height: 1.6; margin: 0;">
    This article is not about comparing languages as such, even if the title may suggest so... it's more of an objective discussion about what errors really are and how to work with them. Of course, I had to start the blog with what it's not, going with the theme of taking care of things that can go wrong :)
    </p><br>
  </div>
  <div style="flex: 0 0 auto;">
    <img 
      src="/assets/imgs/errblog/meme1.png"
      alt="image" 
      style="width: min(200px, 35vw); height: 200px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: block;"
    />
  </div>
</div>


### We need errors

You read that right, errors are one of the best aspects of programming. Folks usually have a dogma or a fear of errors instinctively, cuz they mix them up with what's really the problem - bugs

**So what's the difference?**


<div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 200px;">
    <p style="text-align: justify; line-height: 1.6; margin: 0;">
    Let's derive an analogy from the real world, criminals. Imagine a world without any police or security guards, things would be chaotic and bad all around, but there wouldn't be any news of some arrest, we wouldn't know of most of this stuff except for the folks directly affected by these. That's what bugs are like, generally. If you write a piece of software without any error handling, you would generally be very happy as there are no error popups, or log alerts... but the actual users would not be happy. 
    </p><br>
  </div>
  <div style="flex: 0 0 auto;">
    <img 
      src="/assets/imgs/errblog/analogyone.jpg"
      alt="image" 
      style="width: min(200px, 35vw); height: 200px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: block;"
    />
  </div>
</div>

> What we want to eliminate is undefined software behavior, one way to do that is to have proper error handling

I know this sounds all up in the air right now, bear with me, setting up the example now

### Example scenario

Let's take a typical web dev scenario here, building a backend API that does the following
- fetch exchange rates from `currencyapi.com`
- cache the results for some time
- convert given amount to target currency
- log the conversion request to DB

Cool

### Code it up

This is a simplified scenario you would be dealing with... Let's quickly code it up in python

Here's a working api in python
```python
import os
import json
import requests
import redis
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

CURRENCY_API_URL = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies"
)
CACHE_TTL = 60 * 30
DATABASE_URL = os.getenv("DB_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS rate;"))
    conn.execute(text("SET search_path TO rate;"))

class ConversionLog(Base):
    __tablename__ = "conversion_logs"
    __table_args__ = {"schema": "rate"}

    id = Column(Integer, primary_key=True, index=True)
    base_currency = Column(String, nullable=False)
    target_currency = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    converted_amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        db.execute(text("SET search_path TO rate;"))
        yield db
    finally:
        db.close()

app = FastAPI()

class ConversionRequest(BaseModel):
    amount: float
    base_currency: str
    target_currency: str

def fetch_rates(base_currency: str):
    """Fetch exchange rates JSON from CDN or Redis cache"""
    base_currency = base_currency.lower()
    cache_key = f"rates:{base_currency}"
    if cached := redis_client.get(cache_key):
        return json.loads(cached)
    url = f"{CURRENCY_API_URL}/{base_currency}.json"
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch exchange rates")
    data = response.json()
    rates = data[base_currency]
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(rates))
    return rates

@app.post("/convert")
def convert(req: ConversionRequest, db: Session = Depends(get_db)):
    base = req.base_currency.lower()
    target = req.target_currency.lower()
    rates = fetch_rates(base)
    if target not in rates:
        raise HTTPException(status_code=400, detail="Invalid target currency")
    rate = rates[target]
    converted_amount = req.amount * rate
    log = ConversionLog(
        base_currency=base.upper(),
        target_currency=target.upper(),
        amount=req.amount,
        converted_amount=converted_amount,
    )
    db.add(log)
    db.commit()
    return {
        "base_currency": base.upper(),
        "target_currency": target.upper(),
        "amount": req.amount,
        "converted_amount": converted_amount,
        "rate": rate,
    }
```
Here's what we're doing here
- Define constants, get DB/Redis urls from envs
- Connect to Redis, and DB
- Create and switch to `rates` schema in DB
- Define Table and migrate
- Define a fastapi with one endpoint `/convert`
- Define a payload model
- In the handler,
  - deserialize request (fastapi+pydantic)
  - fetch rates from external api
  - currency case changes, `400` error
  - convert amount, log to DB
  - return response

> This is just for illustration, and is missing lots of things like connection pooling, structure, etc to make it useful

### What can go wrong? 
Note, we didn't really handle any errors or edge cases here, except basic currency validation. Lots of things can go wrong, here are a few that comes to mind...

- missing/improper envs
- db connection issues
  - connection timeout
  - max connection
  - missing privileges to create schema
  - table already exists, schema mismatch
  - migration history issues
  - database dialect issues
  - etc
- redis connection issues
  - connection timeout
  - client mismatch, e.g. redis cluster
  - cluster quorum issues
  - client max connections
  - data loss due to rdb restore failure
- api server
  - port already bound
  - insufficient cpu
  - incompatible concurrency models
  - dependency mismatch
- external API
  - downtime
  - firewall restrictions
  - authentication/rate limiting issues
  - payload mismatch
- Serialization
  - payload type mismatch
  - structure mismatch
  - (for pre-pydantic python/ pre-zod JS) lack of deserialization, missing logic, attribute errors
  - malformed JSON
  - incomplete payload
  - non serializable fields, (again, dict world)

<img 
  src="/assets/imgs/errblog/whatcangowrong.jpg"
  alt="image" 
/>

### Let's generalize this 
I'd like to categorise bugs largely into these four categories, as follows:

> Note: this just just my point of view based on experience, I'm confident there are other things I haven't accounted for here

Let's see...

#### type bugs 
In programming, we're mostly dealing with data. Here's what any typical program does, especially in the web world
- Read persistent data
- Structure it in memory 
- Perform logic
- Send appropriate requests to other services
- Log what happened
- Return result

With me so far? cool.

Not let's take a look at python from 4 years ago..
Here's what you'd do, say to read a file and process it
- Read text data
- Load it into a dictionary
- Iterate through the dict, have lots of `.get()` and `in` conditions to hopefully get the data you need
- Pass these to utility functions as keyword arguments
- Get the logic back, build a result dictionary
- Dump it to json, and return

> Note: I'm picking on python here because especially back in the day, this is how things were... but the same applies to other dynamic languages like JS and ruby as well

<br>

<div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 200px;">
    <p style="text-align: justify; line-height: 1.6; margin: 0;">
Cool.. so just like that... the developer has to: <br><br>
- Keep track of the huge data model in their head <br>
- Cry a little and do "one line fixes" when things break in production
    </p><br>
  </div>
  <div style="flex: 0 0 auto;">
    <img 
      src="/assets/imgs/errblog/itllprollywork.jpg"
      alt="image" 
      style="width: min(200px, 35vw); height: 200px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: block;"
    />
  </div>
</div>

That's why we should have types. Almost every dynamic language has now caught up, so there's no excuse to not do it

We already started with having Pydantic models for our input payload, that's good, wanna know why?...

```bash
❯ curl http://localhost:8000/convert -X POST
{"detail":[{"type":"missing","loc":["body"],"msg":"Field required","input":null}]}
❯
❯ curl http://localhost:8000/convert -X POST -d '{"amount": 100}
∙ '
{"detail":[{"type":"model_attributes_type","loc":["body"],"msg":"Input should be a valid dictionary or object to extract fields from","input":"{\"amount\": 100}\n"}]}
❯
❯ curl http://localhost:8000/convert -X POST -d '{"amount": 100}' -H 'Content-Type: application/json'
{"detail":[{"type":"missing","loc":["body","base_currency"],"msg":"Field required","input":{"amount":100}},{"type":"missing","loc":["body","target_currency"],"msg":"Field required","inpu~
❯
❯ curl http://localhost:8000/convert -X POST -H 'Content-Type: application/json' -d '{"amount": 100, "base_currency": "INR", "target_currency": "USD"}'
{"base_currency":"INR","target_currency":"USD","amount":100.0,"converted_amount":1.1354251,"rate":0.011354251}
```

If we just had a dictionary here, all the user would've seen would be a big fat internal server error, unless you have proper validation logic that checks if the keys are in the right place, and runtime type checks on the values... which can get very messy. 


Let's look at our `fetch_rates` function...

```python
def fetch_rates(base_currency: str):
    """Fetch exchange rates JSON from CDN or Redis cache"""
    base_currency = base_currency.lower()
    cache_key = f"rates:{base_currency}"
    if cached := redis_client.get(cache_key):
        return json.loads(cached)
    url = f"{CURRENCY_API_URL}/{base_currency}.json"
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch exchange rates")
    data = response.json()
    rates = data[base_currency]
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(rates))
    return rates

```

Do you see anything wrong here? No, okay... what happens if the currency api changed it's format? what if it's returning stale data...

This will just result in a `JsonDecodeError` or a `KeyError`... having another model would take care of these. 

> This articls is not about convincing folks to have proper types... but it's important to understand that it's not a thing that's `nice to do`, having compile time checks can let you model your application's spec properly, and takes off a lot of the cognitive load... especially if you're using a proper static type system

#### Logic bugs
Unintuitively, logic bugs are relatively very rare, because most of the applications we write nowadays is mostly gluing things around, instead of specialized logic... 

There are definitely instances where these could happen,
e.g.
- low level networking systems like proxies, databases
- business systems like financial accounting, charges 
- notification systems, etc

But there's a twist...

There could be logic errors in dependencies and other low level systems we use, that could lead to errors we need to handle. More about that in the next section

#### environmental bugs 
Much like a car has to interact with the external world, and can be drastically affected by various factors like:
- potholes/swamps
- lane markers
- traffic signs
- other cars
- traffic
- fuel

our application containers are also affected by stuff like:
- available resources
- environment variables
- other processes
- kernal interrupts

and so on...

And each of these systems need to handle and propagate their errors to us in a meaninful way, so we can handle them accordingly

and so on...

And each of these systems need to handle and propagate their errors to us in a meaninful way, so we can handle them accordingly...

Having a few cars to follow makes it easier in terms of navigation, much like delegating common yet complex tasks to other services, e.g. redis, queues etc make it easier to run our applications, but that definitely increases the failure points and the error surface area we need to cover

> That's an argument for a different blog post, framework vs minimal dependencies

- misconfigurations
- resource exhaustion
-- dependency errors
- essentials connections, inter service rpc, broker nuances
... point out fault tolerance

#### memory bugs 
- nil pointer deref
- out of bounds


### introduce errors as values

- go example
- function stack.. 
- no side effects
- no cognitive load
- verbosity..

### ? operator
- what it solves
- how it can be misused, solutions
- ease into rust traits

###  Error propagation
- error codes
- internationalization needs
- org standardization
- configurable messages
... introduce standard errors

### closing thoughts
