FROM python:3.10-slim

WORKDIR /app

# Install Redis + Node.js for frontend
RUN apt-get update && apt-get install -y \
    redis-server \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy Redis config
COPY redis.conf /usr/local/etc/redis/redis.conf

# ---------- Frontend ----------
WORKDIR /app/frontend
COPY Frontend/package.json Frontend/package-lock.json ./
RUN npm install
COPY Frontend/ .
ARG ADOBE_EMBED_API_KEY
ENV REACT_APP_ADOBE_CLIENT_ID=${ADOBE_EMBED_API_KEY}
RUN npm run build

# ---------- Backend ----------
WORKDIR /app
COPY Backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY Backend/ .

# Copy start.sh to root
COPY Backend/start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh

RUN chmod +x /start.sh

EXPOSE 8080 6379

CMD ["/start.sh"]
