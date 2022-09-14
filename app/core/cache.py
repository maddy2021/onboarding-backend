import json
import pickle
import redis

cache_obj = redis.Redis(host="localhost", port=6379)

def set_cache(key, value, expiry_time=None):
    if(isinstance(value,str)):
        cache_obj.set(key,value,ex=expiry_time)
    # elif(isinstance(value,list)):
    #     cache_obj.set(key, json.dumps(value))
    # elif(isinstance(value,dict)):
    #     cache_obj.set(key, json.dumps(value))
    else:
        cache_obj.set(key, pickle.dumps(value),ex=expiry_time)
    
def get_cache(key):
    value = cache_obj.get(key)
    if(value):
        if(isinstance(value,str)):
            return str(value)
        # elif():
        #     return json.loads(value)
        # elif(isinstance(json.loads(value),dict)):
        #     return json.loads(value)
        # else:
        #     return ""
        else:
            return pickle.loads(cache_obj.get(key))
    else:
        return ""

def get_all_cache():
    print(cache_obj.keys())
    return cache_obj.keys()

def remove_all_cache():
    return cache_obj.flushdb()

def delete_cache(key):
    value = cache_obj.get(key)
    if(value):
        cache_obj.delete(key)

def delete_cache_by_prefix(prefix):
    for key in cache_obj.scan_iter(f"{prefix}*"):
        cache_obj.delete(key)
    

# cache_obj.delete()