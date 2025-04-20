

## Requirements:

- Python version >= 3.9
- 

## Setup:

```
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## Run the code:

```
python main.py sample.yaml

# There's a secondary yaml file I created to test some of the requirements as well

python main.py test.yaml

```

## Notes

Notes and thought process as I go through this exercise:

## Reading through the repo

- there's no dependency file in the repository and we use libraries outside of STL for python like yaml and requests so we'll need to install those and keep track of these
    - I used python3's built in function to setup a separate virtual environment, defined the necessary packages in a pyproject.toml and installed them.
- Reading through the code in main.py, it looks to try to read in a YAML file consisting of REST request definitions and executing those in a loop to keep track of the availability percentage of each endpoint
- Next step I took is to execute the program and just see what sort of errors return given the current state of the codebase
```
    method=method.upper(),
           ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'upper'
```
- Empty object is being passed into the request() call. Going to set a breakpoint in the program and debug the values of the variables
  
- We need to add a default HTTP method, GET, for every request
```
    if not method:
        method = "GET"
```

- Now program executes now and prints that the domain has 25% availability percentage but we need to verify that the other requirements are correct

## Implementing requirements

- Must use either the provided Go or Python code as your starting point; done
- Must accept a YAML configuration as command line argument; done
- YAML format must match that in the sample provided; done
- Must accurately determine the availability of all endpoints during every check cycle
    I was able to confirm through the above execution of the code that the code already was able to 
    accomplish this.

- Endpoints are only considered available if they meet the following conditions
    - Status code is between 200 and 299
    - Endpoint responds in 500ms or less
    I was able to confirm also above that the status code portion was already
    able to only consider endpoints available between 200 and 299. In order to
    validate that endpoints were responding in 500ms or less, I used the time
    library to measure the execution time of request and added a check that it's
    within the range. time.monotonic() was used because of one of the following
    requirements but it is because this function will be called asynchronously so
    it will need to use this instead of time.time()
```
    startTime = time.monotonic()
    requestResponseTime = (time.monotonic() - startTime) * 1000 # need time in ms
    # print("ms" , requestResponseTime)
    if 200 <= response.status < 300 and requestResponseTime <= 500:
        return "UP", domain
    else:
        return "DOWN", domain
```
- Must determine availability cumulatively
done in the original codebase
- Must return availability by domain
done in the original codebase
- Must ignore port numbers when determining domain
modified the endpoint split to check if the char : exists first and either
split on : or /
```
    for endpoint in config:
        domain = endpoint["url"].split("//")[-1]
        if ':' in domain:
            domain = domain.split(":")[0]
        else:
            domain = domain.split("/")[0]
```

- Check cycles must run and log availability results every 15 seconds regardless of the number of endpoints or their response times


In the event of a large file of GBs or TB size, this would quickly start to go past
the 15 seconds requirement as we scale this out. Thus, we need to make these 
requests concurrently using asychronous processes. All of the methods were changed
in order to make the program completely asychronous and in order to not run into
any dataloss or race conditions so I will not go over all of the changes but will
make a note of some key parts of it. 

### Timings
the below code will have the request timeout after 14 seconds. I chose to do this for 14 seconds 
instead of 15 because the when the asynchronous calls are awaited, `await asyncio.gather(*requests)` 
it can take up to a second for it to complete, as well as the time for the execution of the rest of 
the code like the for loops. 
    There may be a way to have a more exact way to maxmize the amount of time for the request, ie 
calculating the time for loops later in the program, but this seemed appropriate for the exercise.

```
    timeout = 14
    ...
        async with session.request(
                    method, url, headers=headers, timeout=timeout, json=body
                ) as response:
```
