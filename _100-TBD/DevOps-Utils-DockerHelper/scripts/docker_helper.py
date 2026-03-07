import os
import sys
import json
import argparse


# ── Templates ─────────────────────────────────────────────────────────────────

TEMPLATES = {
    "python": {
        "dockerfile": """\
FROM python:{version}-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python3", "{entrypoint}"]
""",
        "compose": """\
version: "3.9"
services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    env_file:
      - .env
    restart: unless-stopped
""",
        "version": "3.12",
        "port": "8000",
        "entrypoint": "main.py",
    },
    "node": {
        "dockerfile": """\
FROM node:{version}-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE {port}
CMD ["node", "{entrypoint}"]
""",
        "compose": """\
version: "3.9"
services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    env_file:
      - .env
    restart: unless-stopped
""",
        "version": "22",
        "port": "3000",
        "entrypoint": "index.js",
    },
    "go": {
        "dockerfile": """\
FROM golang:{version}-alpine AS builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN go build -o app .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/app .
EXPOSE {port}
CMD ["./app"]
""",
        "compose": """\
version: "3.9"
services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    env_file:
      - .env
    restart: unless-stopped
""",
        "version": "1.23",
        "port": "8080",
        "entrypoint": "main.go",
    },
    "rust": {
        "dockerfile": """\
FROM rust:{version}-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /app/target/release/app .
EXPOSE {port}
CMD ["./app"]
""",
        "compose": """\
version: "3.9"
services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    restart: unless-stopped
""",
        "version": "1.82",
        "port": "8080",
        "entrypoint": "src/main.rs",
    },
    "java": {
        "dockerfile": """\
FROM eclipse-temurin:{version}-jdk-alpine AS builder
WORKDIR /app
COPY . .
RUN ./mvnw package -DskipTests 2>/dev/null || ./gradlew build -x test

FROM eclipse-temurin:{version}-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar 2>/dev/null || \
     COPY --from=builder /app/build/libs/*.jar app.jar
EXPOSE {port}
CMD ["java", "-jar", "app.jar"]
""",
        "compose": """\
version: "3.9"
services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    env_file:
      - .env
    restart: unless-stopped
""",
        "version": "21",
        "port": "8080",
        "entrypoint": "src/main/java/Main.java",
    },
    "ruby": {
        "dockerfile": """\
FROM ruby:{version}-slim
WORKDIR /app
COPY Gemfile Gemfile.lock ./
RUN bundle install
COPY . .
EXPOSE {port}
CMD ["bundle", "exec", "ruby", "{entrypoint}"]
""",
        "compose": """\
version: "3.9"
services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    env_file:
      - .env
    restart: unless-stopped
""",
        "version": "3.3",
        "port": "3000",
        "entrypoint": "app.rb",
    },
}

DETECTORS = {
    "python": ["requirements.txt", "pyproject.toml", "setup.py"],
    "node":   ["package.json"],
    "go":     ["go.mod"],
    "rust":   ["Cargo.toml"],
    "java":   ["pom.xml", "build.gradle"],
    "ruby":   ["Gemfile"],
}


def _detect_lang(directory: str) -> str | None:
    files = set(os.listdir(directory))
    for lang, indicators in DETECTORS.items():
        if any(ind in files for ind in indicators):
            return lang
    return None


def _find_port(directory: str, lang: str) -> str:
    """Try to extract port from common config files."""
    port_hints = {
        "python": [("requirements.txt", None), (".env", "PORT")],
        "node":   [("package.json", None)],
    }
    return TEMPLATES[lang]["port"]


def _render(template: str, lang: str, port: str) -> str:
    t = TEMPLATES[lang]
    return template.format(version=t["version"], port=port, entrypoint=t["entrypoint"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Dockerfile from project analysis.")
    parser.add_argument("--dir",     default=".", help="Project directory (default: .)")
    parser.add_argument("--output",  default=None, help="Directory to save files (default: stdout)")
    parser.add_argument("--lang",    default=None, help="Override language detection")
    parser.add_argument("--port",    default=None, help="Override port")
    parser.add_argument("--compose", action="store_true", help="Also generate docker-compose.yml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    directory = os.path.abspath(args.dir)
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' not found."); sys.exit(1)

    lang = args.lang or _detect_lang(directory)
    if not lang:
        print("Error: Could not detect stack. Use --lang to specify."); sys.exit(1)
    if lang not in TEMPLATES:
        print(f"Error: No template for lang '{lang}'. Supported: {', '.join(TEMPLATES)}"); sys.exit(1)

    port = args.port or _find_port(directory, lang)
    print(f"Detected stack: {lang}  |  Port: {port}")

    dockerfile = _render(TEMPLATES[lang]["dockerfile"], lang, port)
    compose = _render(TEMPLATES[lang]["compose"], lang, port) if args.compose else None

    if args.dry_run or not args.output:
        print("\n# Dockerfile\n")
        print(dockerfile)
        if compose:
            print("\n# docker-compose.yml\n")
            print(compose)
    else:
        df_path = os.path.join(args.output, "Dockerfile")
        with open(df_path, "w") as f:
            f.write(dockerfile)
        print(f"Saved: {df_path}")
        if compose:
            dc_path = os.path.join(args.output, "docker-compose.yml")
            with open(dc_path, "w") as f:
                f.write(compose)
            print(f"Saved: {dc_path}")


if __name__ == "__main__":
    main()
