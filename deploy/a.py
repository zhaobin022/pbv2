d = [
    {
        "id": 7,
        "environment": {
            "id": 2,
            "app_var": [
                {
                    "id": 24,
                    "key": "a",
                    "value": "b",
                    "environment": 2
                },
                {
                    "id": 25,
                    "key": "c",
                    "value": "d",
                    "environment": 2
                }
            ],
            "db_var": [
                {
                    "id": 4,
                    "key": "e",
                    "value": "f",
                    "environment": 2
                },
                {
                    "id": 5,
                    "key": "g",
                    "value": "k",
                    "environment": 2
                }
            ],
            "environment_name": "119"
        },
        "group": {
            "id": 3,
            "name": "g3"
        },
        "tomcat": None,
        "hosts": [
            {
                "id": 1,
                "host_type": "app",
                "ipaddr": "127.0.0.1"
            }
        ],
        "group_type": "javaapps",
        "app_variables": [],
        "db_variables": [],
        "priority": 3,
        "project": 1,
        "app_foot": 2,
        "templates": []
    },
    {
        "id": 1,
        "environment": {
            "id": 2,
            "app_var": [
                {
                    "id": 24,
                    "key": "a",
                    "value": "b",
                    "environment": 2
                },
                {
                    "id": 25,
                    "key": "c",
                    "value": "d",
                    "environment": 2
                }
            ],
            "db_var": [
                {
                    "id": 4,
                    "key": "e",
                    "value": "f",
                    "environment": 2
                },
                {
                    "id": 5,
                    "key": "g",
                    "value": "k",
                    "environment": 2
                }
            ],
            "environment_name": "119"
        },
        "group": {
            "id": 1,
            "name": "g1"
        },
        "tomcat": None,
        "hosts": [
            {
                "id": 1,
                "host_type": "app",
                "ipaddr": "127.0.0.1"
            },
            {
                "id": 2,
                "host_type": "app",
                "ipaddr": "127.0.0.2"
            }
        ],
        "group_type": "javaapps",
        "app_variables": [],
        "db_variables": [],
        "priority": 2,
        "project": 1,
        "app_foot": 1,
        "templates": []
    },
    {
        "id": 2,
        "environment": {
            "id": 2,
            "app_var": [
                {
                    "id": 24,
                    "key": "a",
                    "value": "b",
                    "environment": 2
                },
                {
                    "id": 25,
                    "key": "c",
                    "value": "d",
                    "environment": 2
                }
            ],
            "db_var": [
                {
                    "id": 4,
                    "key": "e",
                    "value": "f",
                    "environment": 2
                },
                {
                    "id": 5,
                    "key": "g",
                    "value": "k",
                    "environment": 2
                }
            ],
            "environment_name": "119"
        },
        "group": {
            "id": 2,
            "name": "ag2"
        },
        "tomcat": {
            "id": 1,
            "http_type": "http",
            "name": "a-tomcat8",
            "shutdown_port": 1000,
            "http_port": 2000,
            "https_port": 3000,
            "jvm_size": 2048
        },
        "hosts": [
            {
                "id": 1,
                "host_type": "app",
                "ipaddr": "127.0.0.1"
            }
        ],
        "group_type": "webapps",
        "app_variables": [],
        "db_variables": [],
        "priority": 1,
        "project": 1,
        "app_foot": None,
        "templates": []
    }
]

l = []
for i in d:
    temp = {}
    if i['group_type'] == 'javaapps':
        temp['name'] = "%s_%s" % (i['group']['name'])

