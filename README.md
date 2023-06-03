# Toggl Track Companion

[![Source](https://badgen.net/badge/icon/Source?icon=github&label)](https://github.com/jan-di/toggl-track-companion)
[![Checks](https://badgen.net/github/checks/jan-di/toggl-track-companion)](https://github.com/jan-di/toggl-track-companion/actions/workflows/build.yml)
[![Release](https://badgen.net/github/release/jan-di/toggl-track-companion/stable)](https://github.com/jan-di/toggl-track-companion/releases)
[![Last Commit](https://badgen.net/github/last-commit/jan-di/toggl-track-companion/main)](https://github.com/jan-di/toggl-track-companion/commits/main)
[![License](https://badgen.net/github/license/jan-di/toggl-track-companion)](https://github.com/jan-di/toggl-track-companion/blob/main/LICENSE)

Toggl Track Companion is a web based application to give you addional views and reports for your Toggl Track account.

## Self Hosting

Toggl Track Companion is designed to run in containers. Make sure to have a running docker setup with docker compose.

`docker-compose.yml`

```yml
# sample config to run toggl track companion with traefik as a reverse proxy

services:
  mongodb:
    image: docker.io/mongo:latest
    restart: unless-stopped
    volumes:
      - ./mongodb/data:/data/db
      - ./mongodb/config/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    env_file:
      - ./mongodb/config/mongodb.env
    labels:
      - com.centurylinklabs.watchtower.enable=true
    networks:
      - internal

  web:
    image: ghcr.io/jan-di/toggl-track-companion:main
    restart: unless-stopped
    command: web
    labels:
      - com.centurylinklabs.watchtower.enable=true
      - traefik.enable=true
      - traefik.http.routers.toggl-track-companion.entryPoints=https
      - traefik.http.routers.toggl-track-companion.rule=Host(`toggl-track-companion.example`)
      - traefik.http.routers.toggl-track-companion.tls=true
      - traefik.http.services.toggl-track-companion.loadbalancer.server.scheme=http
      - traefik.http.services.toggl-track-companion.loadbalancer.server.port=5000
    env_file:
      - ./companion/companion.env
    networks:
      - internal
      - reverse-proxy
    depends_on:
      - mongodb

  updater:
    image: ghcr.io/jan-di/toggl-track-companion:main
    restart: unless-stopped
    command: updater
    labels:
      - com.centurylinklabs.watchtower.enable=true
    env_file:
      - ./companion/companion.env
    networks:
      - internal
    depends_on:
      - mongodb

networks:
  internal:
    external: false
  reverse-proxy:
    external: true
```

`mongodb/config/mongodb.env`

```shell
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=<secure-password-for-root-user>
MONGO_INITDB_DATABASE=app
```

`mongodb/config/mongo-init.js`

```js
db.createUser({
  user: "app",
  pwd: "<secure-password-for-app-user>",
  roles: [{ role: "dbOwner", db: "app" }],
});

db.grantRolesToUser("app", [{ role: "clusterMonitor", db: "admin" }]);
```

`companion/companion.env`

```shell
DATABASE_URI = 'mongodb://app:<secure-password-for-app-user>@mongodb:27017/app'
FLASK_SERVER_NAME = "<the-url-to-reach-webserver>"
FLASK_SESSION_SECRET = "<random-generated-session-secret>"
SYNC_INTERVAL_CALENDAR = 900
SYNC_INTERVAL_TOGGL = 3600
```

### Configuration

| Variable                 | Default  | Description                                      |
| ------------------------ | -------- | ------------------------------------------------ |
| `DATABASE_URI`           | required | URL to Mongodb database.                         |
| `FLASK_SERVER_NAME`      | required | Server Host/Port that clients use to connect.    |
| `FLASK_SESSION_SECRET`   | required | Random string that is used to sign session keys. |
| `SYNC_INTERVAL_CALENDAR` | `3600`   | Sync interval for schedule calendars in seconds  |
| `SYNC_INTERVAL_TOGGL`    | `86400`  | Sync interval for toggl data in seconds          |
