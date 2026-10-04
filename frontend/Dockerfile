FROM node:22-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# The API address is baked into the build (Vite replaces import.meta.env.VITE_API_URL at build time).
# It is the address the BROWSER uses to reach the backend, so it must be reachable from your machine.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

EXPOSE 5173
CMD ["npm", "run", "preview"]
