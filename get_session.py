import requests
s = requests.Session()
API_URL = "http://localhost/Caleminder/database/session_api.php"
res = s.get(API_URL)

print("PHPSESSID:", s.cookies.get("PHPSESSID"))
print("API Response:", res.text)

var = s.cookies.get("PHPSESSID")


