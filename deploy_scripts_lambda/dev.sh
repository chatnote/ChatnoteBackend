# zappa_settings.py 파일 생성
zappa save-python-settings-file dev

# docker image build and tagging
TAG="lambda-$(date +"%Y-%m-%d-%H-%M-%S")"
IMAGE_NAME=chatnote_dev
ECR_PATH=974539925060.dkr.ecr.ap-northeast-2.amazonaws.com/$IMAGE_NAME

docker build -t $IMAGE_NAME:$TAG . -f dockerfiles/dev.lambda.Dockerfile
docker tag $IMAGE_NAME:$TAG $ECR_PATH:$TAG

# ecr push
docker run --rm -it -v ~/.aws:/root/.aws -v $(pwd):/aws amazon/aws-cli ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin $ECR_PATH:$TAG
docker push $ECR_PATH:$TAG

# zappa update and update api gateway
zappa update dev -d $ECR_PATH:$TAG

# zappa_settings.py 파일 삭제 및 로컬 docker image 삭제
rm -r zappa_settings.py
DELETING_IMAGES_1=$(docker images -f "dangling=true" -q)
DELETING_IMAGES_2=$(docker images --filter=reference='chatnote_dev*:*' -q)

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
