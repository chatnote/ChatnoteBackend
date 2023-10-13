IMAGE_NAME=chatnote_dev
TAG=$(date +"%Y-%m-%d-%H-%M-%S")
ECR_PATH=974539925060.dkr.ecr.ap-northeast-2.amazonaws.com/$IMAGE_NAME
task_container_name="chatnote"
ecs_execution_role_arn="arn:aws:iam::974539925060:role/ecsTaskExecutionRole"
task_definition_json=$(python3 deploy_scripts/task_definitions.py "$ECR_PATH:$TAG" "$task_container_name" "$ecs_execution_role_arn")
ecs_cluster="chatnote_dev"
ecs_service="chatnoe"

DELETING_IMAGES_1=$(docker images -f "dangling=true" -q)
DELETING_IMAGES_2=$(docker images --filter=reference="${IMAGE_NAME}*:*" -q)


if [[ -z "${DELETING_IMAGES_1}" ]]; then
  echo "There's no dangling=true images"
else
  docker rmi ${DELETING_IMAGES_1}
  echo "Delete dangling=true images"
fi

if [[ -z "${DELETING_IMAGES_2}" ]]; then
  echo "There's no created images"
else
  docker rmi -f ${DELETING_IMAGES_2}
  echo "Delete created images"
fi

# docker build
docker build -t $IMAGE_NAME:$TAG . -f dockerfiles/dev.Dockerfile
docker tag $IMAGE_NAME:$TAG $ECR_PATH:$TAG
echo "==========docker build 완료=========="

# ecr push
docker run --rm -it -v ~/.aws:/root/.aws -v $(pwd):/aws amazon/aws-cli ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin $ECR_PATH:$TAG
docker push $ECR_PATH:$TAG
echo "==========ecr push 완료=========="

# register ecs task definition
register_task_definition_output=$(docker run --rm -it -v ~/.aws:/root/.aws -v "$(pwd)":/aws amazon/aws-cli ecs register-task-definition --cli-input-json "$task_definition_json")
echo "==========ecs task definition register 완료=========="
echo "$register_task_definition_output"

## update service
#task_definition_arn=$(echo "$register_task_definition_output" | jq -r '.taskDefinition.taskDefinitionArn')
#docker run --rm -it -v ~/.aws:/root/.aws -v $(pwd):/aws amazon/aws-cli ecs update-service --cluster "$ecs_cluster" --service "$ecs_service" --task-definition "$task_definition_arn"
#echo "==========ecs service update 완료=========="
