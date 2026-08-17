#!/bin/bash

# Kubernetes Deployment Script for FieldMind
# 用于部署FieldMind到Kubernetes集群

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="fieldmind"
IMAGE_TAG=${1:-latest}

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}FieldMind Kubernetes Deployment${NC}"
echo -e "${GREEN}Namespace: ${NAMESPACE}${NC}"
echo -e "${GREEN}Image Tag: ${IMAGE_TAG}${NC}"
echo -e "${GREEN}=====================================${NC}"

# 检查kubectl
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}错误: kubectl未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ kubectl已安装${NC}"
}

# 检查集群连接
check_cluster() {
    echo -e "${YELLOW}检查集群连接...${NC}"
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}错误: 无法连接到Kubernetes集群${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ 集群连接正常${NC}"
}

# 创建命名空间
create_namespace() {
    echo -e "${YELLOW}创建命名空间...${NC}"
    kubectl apply -f k8s/namespace.yaml
    echo -e "${GREEN}✓ 命名空间已创建${NC}"
}

# 创建ConfigMap和Secret
create_configs() {
    echo -e "${YELLOW}创建配置...${NC}"

    # 检查Secret是否需要更新
    if kubectl get secret fieldmind-backend-secret -n ${NAMESPACE} &> /dev/null; then
        echo -e "${YELLOW}! Secret已存在，跳过创建${NC}"
    else
        kubectl apply -f k8s/configmap.yaml
        echo -e "${GREEN}✓ ConfigMap和Secret已创建${NC}"
    fi
}

# 创建PVC
create_pvcs() {
    echo -e "${YELLOW}创建持久卷...${NC}"
    kubectl apply -f k8s/pvc.yaml
    echo -e "${GREEN}✓ PVC已创建${NC}"
}

# 部署Redis
deploy_redis() {
    echo -e "${YELLOW}部署Redis...${NC}"
    kubectl apply -f k8s/redis-statefulset.yaml

    echo "等待Redis就绪..."
    kubectl wait --for=condition=ready pod -l app=redis -n ${NAMESPACE} --timeout=300s
    echo -e "${GREEN}✓ Redis已部署${NC}"
}

# 部署Neo4j
deploy_neo4j() {
    echo -e "${YELLOW}部署Neo4j...${NC}"
    kubectl apply -f k8s/neo4j-statefulset.yaml

    echo "等待Neo4j就绪..."
    kubectl wait --for=condition=ready pod -l app=neo4j -n ${NAMESPACE} --timeout=600s
    echo -e "${GREEN}✓ Neo4j已部署${NC}"
}

# 部署Backend
deploy_backend() {
    echo -e "${YELLOW}部署Backend...${NC}"

    # 更新镜像标签
    if [ "$IMAGE_TAG" != "latest" ]; then
        sed -i.bak "s|fieldmind/backend:latest|fieldmind/backend:${IMAGE_TAG}|g" k8s/backend-deployment.yaml
    fi

    kubectl apply -f k8s/backend-deployment.yaml

    echo "等待Backend就绪..."
    kubectl wait --for=condition=available deployment/fieldmind-backend -n ${NAMESPACE} --timeout=600s

    # 恢复文件
    if [ "$IMAGE_TAG" != "latest" ] && [ -f "k8s/backend-deployment.yaml.bak" ]; then
        mv k8s/backend-deployment.yaml.bak k8s/backend-deployment.yaml
    fi

    echo -e "${GREEN}✓ Backend已部署${NC}"
}

# 部署HPA
deploy_hpa() {
    echo -e "${YELLOW}部署自动扩缩容...${NC}"
    kubectl apply -f k8s/hpa.yaml
    echo -e "${GREEN}✓ HPA已部署${NC}"
}

# 部署Ingress
deploy_ingress() {
    echo -e "${YELLOW}部署Ingress...${NC}"
    kubectl apply -f k8s/ingress.yaml
    echo -e "${GREEN}✓ Ingress已部署${NC}"
}

# 运行数据库迁移
run_migrations() {
    echo -e "${YELLOW}运行数据库迁移...${NC}"

    POD=$(kubectl get pod -n ${NAMESPACE} -l app=fieldmind-backend -o jsonpath="{.items[0].metadata.name}")

    if [ -n "$POD" ]; then
        kubectl exec -n ${NAMESPACE} ${POD} -- alembic upgrade head || true
        echo -e "${GREEN}✓ 数据库迁移完成${NC}"
    else
        echo -e "${YELLOW}! 未找到Backend Pod${NC}"
    fi
}

# 健康检查
health_check() {
    echo -e "${YELLOW}执行健康检查...${NC}"

    POD=$(kubectl get pod -n ${NAMESPACE} -l app=fieldmind-backend -o jsonpath="{.items[0].metadata.name}")

    if [ -n "$POD" ]; then
        kubectl exec -n ${NAMESPACE} ${POD} -- curl -f http://localhost:8000/health
        echo -e "${GREEN}✓ 健康检查通过${NC}"
    else
        echo -e "${RED}错误: 未找到Backend Pod${NC}"
        exit 1
    fi
}

# 显示部署信息
show_info() {
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}部署完成！${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    echo -e "查看Pods: ${YELLOW}kubectl get pods -n ${NAMESPACE}${NC}"
    echo -e "查看服务: ${YELLOW}kubectl get svc -n ${NAMESPACE}${NC}"
    echo -e "查看Ingress: ${YELLOW}kubectl get ingress -n ${NAMESPACE}${NC}"
    echo ""
    echo -e "Backend日志: ${YELLOW}kubectl logs -f -l app=fieldmind-backend -n ${NAMESPACE}${NC}"
    echo -e "端口转发: ${YELLOW}kubectl port-forward svc/fieldmind-backend-service 8000:8000 -n ${NAMESPACE}${NC}"
    echo ""
}

# 主流程
main() {
    check_kubectl
    check_cluster
    create_namespace
    create_configs
    create_pvcs
    deploy_redis
    deploy_neo4j
    deploy_backend
    deploy_hpa
    deploy_ingress
    run_migrations
    health_check
    show_info
}

trap 'echo -e "${RED}部署失败！${NC}"; exit 1' ERR

main
