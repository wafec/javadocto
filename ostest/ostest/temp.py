from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

from urllib.parse import urlparse

auth = v3.Password(auth_url="http://localhost/identity/v3", username="admin",
                   password="supersecret", project_name="admin",
                   user_domain_id="default", project_domain_id="default")
sess = session.Session(auth=auth)
keystone = client.Client(session=sess)

updates = []

for endpoint in keystone.endpoints.list():
    o = urlparse(endpoint.url)
    service = keystone.services.get(endpoint.service_id)
    updates.append((endpoint.id, f"{o.scheme}://localhost:8888{o.path}", service.type, endpoint.url))

for update in updates:
    keystone.endpoints.update(endpoint=update[0], url=update[1])

for endpoint in keystone.endpoints.list():
    print(endpoint.url)

for update in updates:
    keystone.endpoints.update(endpoint=update[0], url=update[3])
