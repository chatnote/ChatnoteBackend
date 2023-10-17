import json
import sys


def task_definition(_image_name: str, _container_name: str, _execution_role_arn: str):
    data = {
        "containerDefinitions": [
            {
                "name": _container_name,
                "image": _image_name,
                "cpu": 0,
                "portMappings": [
                    {
                        "name": "chatnote-8000-tcp",
                        "containerPort": 8000,
                        "hostPort": 8000,
                        "protocol": "tcp",
                        "appProtocol": "http"
                    }
                ],
                "essential": True,
                "environment": [],
                "environmentFiles": [],
                "mountPoints": [],
                "volumesFrom": [],
                "ulimits": [],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-create-group": "true",
                        "awslogs-group": "/ecs/chatnote_dev",
                        "awslogs-region": "ap-northeast-2",
                        "awslogs-stream-prefix": "ecs"
                    },
                    "secretOptions": []
                }
            }
        ],
        "family": "chatnote_dev",
        "executionRoleArn": _execution_role_arn,
        "networkMode": "awsvpc",
        "volumes": [],
        "placementConstraints": [],
        "requiresCompatibilities": [
            "FARGATE"
        ],
        "cpu": "1024",
        "memory": "3072",
        "runtimePlatform": {
            "cpuArchitecture": "ARM64",
            "operatingSystemFamily": "LINUX"
        },
    }

    return json.dumps(data)


image_name = sys.argv[1]
container_name = sys.argv[2]
execution_role_arn = sys.argv[3]

result = task_definition(image_name, container_name, execution_role_arn)
print(result)
