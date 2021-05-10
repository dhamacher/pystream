# Container registry name
acr_registry = dhamacher

# Values for test repo and tags
acr_repo = pystream-tst
git_repo = pystream-tst
udp_tag = pystream-udp
tcp_tag = pystream-tcp


build:
	docker build -f "Dockerfile.udp" -t $(git_repo):$(udp_tag) "."
	docker build -f "Dockerfile.tcp" -t $(git_repo):$(tcp_tag) "."

build-azure: build	
	docker login $(acr_registry).azurecr.io
	docker tag $(git_repo):$(udp_tag) $(acr_registry).azurecr.io/$(acr_repo):$(udp_tag)
	docker tag $(git_repo):$(tcp_tag) $(acr_registry).azurecr.io/$(acr_repo):$(tcp_tag)
	
	docker push $(acr_registry).azurecr.io/$(acr_repo):$(udp_tag)
	docker push $(acr_registry).azurecr.io/$(acr_repo):$(tcp_tag)

run:
	docker-compose up
