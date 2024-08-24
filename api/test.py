import requests

base_url = "http://127.0.0.1:5000/"


response = requests.get(base_url + "helloworld/joe")
print(response.json())

input()
response = requests.put(base_url + "helloworld/joe", {"name": "Joe", "money": 10, "family": 100})

# response = requests.put(base_url + "video/4", {"name": "Joe", "likes": 10, "views": 100})
# print(response.json())

# input()
# response = requests.patch(base_url + "video/4", {"views": 333}) 
# print(response.json())

# input()
# response = requests.patch(base_url + "video/5", {"name": "joe", "likes": 11, "views": 111})
# print(response.json())

# input()
# response = requests.delete(base_url + "video/4")
# print(response)

# input()
# response = requests.get(base_url + "video/4")
# print(response.json())