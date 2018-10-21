from openhurricane import drivers
from munch import munchify


def test_driver_initialization():
    CONF = {
        "auth": {
            "url": "http://localhost/identity/v3",
            "username": "admin",
            "password" : "supersecret",
            "user_domain_id": "default",
            "project_domain_id": "default",
            "project_name": "admin"
        },
        "resources": {
            "image": {
                "id": "100050",
                "name": "image100050",
                "disk_format": "qcow2",
                "data_file": "./tests/cirros0.3.4.img",
                "container_format": "bare",
                "visibility": "public"
            },
            "image_alt": {
                "id": "100051",
                "name": "image100051",
                "disk_format": "qcow2",
                "data_file": "./tests/cirros0.4.0.img",
                "container_format": "bare",
                "visibility": "public"
            },
            "flavor": {
                "id": "110050",
                "name": "flavor11050",
                "ram": "64",
                "vcpus": "1",
                "disk": "0"
            },
            "flavor_alt": {
                "id": "110051",
                "name": "flavor11051",
                "ram": "128",
                "vcpus": "2",
                "disk": "0"
            },
            "server": {
                "name": "foo"
            }
        }
    }

    test_driver = drivers.ComputeTestDriver(munchify(CONF))
    test_driver.clear()