# bws-docker
The latest Bitwarden Secrets Manager CLI in a Docker container. Includes an API server.

## Instructions
### Interactive CLI
Run `docker build -t bws:latest .`

Then, `docker run --rm bws:latest help`

### Serve API
Create a local API instance:

`docker-compose.yml`
```yaml
---
version: '3.8'
services:
  secrets_api:
    container_name: secrets_api
    image: secrets_api
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - 5000:5000
```