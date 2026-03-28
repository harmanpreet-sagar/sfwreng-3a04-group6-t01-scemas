# Frontend Dockerfile
# Creates containerized React + TypeScript application with Vite build tool

# Use Node.js 20 Alpine for minimal image size
FROM node:20-alpine

# Set working directory inside container
WORKDIR /app

# Copy package files first to leverage Docker layer caching
# Dependencies only rebuild if package.json or package-lock.json changes
COPY package*.json ./
RUN npm install

# Copy application source code
COPY . .

# Expose Vite dev server port
EXPOSE 3000

# Start Vite development server with host binding for Docker access
# --host 0.0.0.0 allows external connections to the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
